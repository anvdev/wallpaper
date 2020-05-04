"""
MIT License

Copyright (c) 2020 Ivan Titov

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

try:
    from PySide2.QtWidgets import *
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    from PySide2.QtSvg import *
except ImportError:
    try:
        from PyQt5.QtWidgets import *
        from PyQt5.QtGui import *
        from PyQt5.QtCore import *
        from PyQt5.QtSvg import *

        Signal = pyqtSignal
    except ImportError:
        from hutil.Qt.QtWidgets import *
        from hutil.Qt.QtGui import *
        from hutil.Qt.QtCore import *
        from hutil.Qt.QtSvg import *

import wallpaper


class ImageView(QLabel):
    def __init__(self):
        super(ImageView, self).__init__()

        self.setMinimumWidth(400)

    def setImage(self, image):
        image = QPixmap(image)
        image = image.scaled(self.width(),
                             self.height(),
                             Qt.KeepAspectRatio,
                             Qt.SmoothTransformation)
        self.setPixmap(image)


class HoudiniSliderStyle(QProxyStyle):
    def __init__(self, style):
        super(HoudiniSliderStyle, self).__init__(style)

    def styleHint(self, hint, option, widget, return_data):
        if hint == QStyle.SH_Slider_AbsoluteSetButtons:
            return Qt.LeftButton
        return super(HoudiniSliderStyle, self).styleHint(hint, option, widget, return_data)


class NumParameter(QWidget):
    # Signals
    valueChanged = Signal()

    def __init__(self, value=0.0, value_range=None, single_step=None):
        super(NumParameter, self).__init__()

        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._type = type(value)

        # Field
        if self._type == int:
            self.field = QSpinBox()
        else:  # self._type == float
            self.field = QDoubleSpinBox()
        self.field.setFixedWidth(60)
        layout.addWidget(self.field)
        self.field.installEventFilter(self)

        # Slider
        self.slider = QSlider(Qt.Horizontal)
        # Todo
        # houdini_slider_style = HoudiniSliderStyle(self.slider.style())
        # self.slider.setStyle(houdini_slider_style)
        layout.addWidget(self.slider)
        self.slider.installEventFilter(self)

        # Data
        if value_range:
            self.setRange(value_range[0], value_range[1])
        elif self._type == int:
            self.setRange(0, 4096)
        else:  # self._type == float:
            self.setRange(0, 100)

        if single_step:
            self.setSingleStep(single_step)

        self.setValue(value)
        self._dvalue = value

        # Connections
        self.field.valueChanged.connect(self._updateValueFromField)
        self.slider.valueChanged.connect(self._updateValueFromSlider)

    def eventFilter(self, obj, event):
        if (obj == self.field or obj == self.slider) and isinstance(event, QMouseEvent):
            if event.button() == Qt.MiddleButton:
                if event.type() == QEvent.MouseButtonRelease and event.modifiers() == Qt.ControlModifier:
                    self.resetToDefault()
                return True
        return super(NumParameter, self).eventFilter(obj, event)

    def _updateValueFromField(self, value):
        self.slider.blockSignals(True)
        if self._type == float:
            value = value * 100
        self.slider.setValue(value)
        self.slider.blockSignals(False)
        self.valueChanged.emit()

    def _updateValueFromSlider(self, value):
        self.field.blockSignals(True)
        if self._type == float:
            value = value / 100.0
        self.field.setValue(value)
        self.field.blockSignals(False)
        self.valueChanged.emit()

    def setRange(self, min_value, max_value):
        self.blockSignals(True)
        self.field.setRange(min_value, max_value)
        if self._type == int:
            self.slider.setRange(min_value, max_value)
        else:  # self._type == float:
            self.slider.setRange(min_value * 100, max_value * 100)
        self.blockSignals(False)

    def setSingleStep(self, value):
        self.blockSignals(True)
        self.field.setSingleStep(value)
        if self._type == int:
            self.slider.setSingleStep(value)
        else:  # self._type == int
            self.slider.setSingleStep(value * 100)
        self.blockSignals(False)

    def setDefaultValue(self, value):
        self._dvalue = value

    def defaultValue(self):
        return self._dvalue

    def setValue(self, value, use_as_default=False):
        self.field.blockSignals(True)
        self.slider.blockSignals(True)

        if use_as_default:
            self.setDefaultValue(value)

        self.field.setValue(value)
        if self._type == int:
            self.slider.setValue(value)
        else:  # self._type == float:
            self.slider.setValue(value * 100)

        self.field.blockSignals(False)
        self.slider.blockSignals(False)
        self.valueChanged.emit()

    def resetToDefault(self):
        self.setValue(self._dvalue)

    def value(self):
        if self._type == int:
            return int(self.field.value())
        else:  # self._value_type == float:
            return self.field.value()


# Todo: hex color validator

class ColorParameter(QWidget):
    # Signals
    valueChanged = Signal(str)

    def __init__(self, color=QColor(Qt.black)):
        super(ColorParameter, self).__init__()

        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Field
        self.field = QLineEdit()
        self.field.setFixedWidth(60)
        layout.addWidget(self.field)
        self.field.installEventFilter(self)

        # Color
        self.color_dialog = QColorDialog(QColor(self.field.text()), self)
        self.color_dialog.currentColorChanged.connect(self.setValue)

        self.color_button = QPushButton()
        self.color_button.clicked.connect(self._pickColor)
        layout.addWidget(self.color_button)
        self.field.installEventFilter(self)

        # Data
        self.setValue(color)
        self._dvalue = color

        # Connections
        self.field.textChanged.connect(self.valueChanged.emit)

    def eventFilter(self, obj, event):
        if obj == self.field and event.type() == QEvent.MouseButtonRelease:
            if event.button() == Qt.MiddleButton and event.modifiers() == Qt.ControlModifier:
                self.resetToDefault()
                return True
        return super(ColorParameter, self).eventFilter(obj, event)

    def _setButtonColor(self, color):
        color = str(QColor(color).toTuple()[:3])
        self.color_button.setStyleSheet('QPushButton {{ background-color: rgb{0}; }}'.format(color))

    def _pickColor(self):
        self.color_dialog.setCurrentColor(QColor(self.field.text()))
        self.color_dialog.show()

    def setDefaultValue(self, value):
        color = QColor(value)
        if not color.isValid():
            return

        self._dvalue = color.name()

    def defaultValue(self):
        return self._dvalue

    def setValue(self, value, use_as_default=False):
        color = QColor(value)
        if not color.isValid():
            return

        value = color.name()

        if use_as_default:
            self.setDefaultValue(value)

        self.field.setText(value)
        self._setButtonColor(color)

        self.valueChanged.emit(value)

    def resetToDefault(self):
        self.setValue(self._dvalue)

    def value(self):
        return self.field.text()


class MainWindow(QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()

        # Window
        self.setWindowTitle('Houdini Wallpaper')
        self.resize(800, 600)

        # Layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # Splitter
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)

        # Image View
        self.view = ImageView()
        main_splitter.addWidget(self.view)
        main_splitter.splitterMoved.connect(lambda: self.view.setImage(self.__image))
        main_splitter.setStretchFactor(0, 1)

        # Parameters
        side_widget = QWidget()
        main_splitter.addWidget(side_widget)
        main_splitter.setStretchFactor(1, 0)

        side_layout = QVBoxLayout(side_widget)
        side_layout.setContentsMargins(0, 0, 0, 0)
        side_layout.setSpacing(4)

        parm_layout = QFormLayout()
        parm_layout.setLabelAlignment(Qt.AlignTop)
        side_layout.addLayout(parm_layout)

        # Width
        self.width_field = NumParameter(1920, (1, 4096), 128)
        self.width_field.setToolTip('The width of the output image (in pixels).')
        self.width_field.valueChanged.connect(self.updateImage)
        parm_layout.addRow('Width', self.width_field)

        # Height
        self.height_field = NumParameter(1080, (1, 4096), 128)
        self.height_field.setToolTip('The height of the output image (in pixels).')
        self.height_field.valueChanged.connect(self.updateImage)
        parm_layout.addRow('Height', self.height_field)

        # Scale
        self.scale_field = NumParameter(0.8, (0.1, 10), 0.1)
        self.scale_field.setToolTip('A scaling factor for the vector art. Use this to make the pattern bigger or smaller.')
        self.scale_field.valueChanged.connect(self.updateImage)
        parm_layout.addRow('Scale', self.scale_field)

        # Rotation
        self.rotation_field = NumParameter(-7.0, (-360, 360))
        self.rotation_field.setToolTip('Rotation of the pattern (in degrees). Negative numbers rotate counter-clockwise.')
        self.rotation_field.valueChanged.connect(self.updateImage)
        parm_layout.addRow('Rotation', self.rotation_field)

        # Slop
        self.slop_field = NumParameter(5, (0, 50), 1)
        self.slop_field.setToolTip("Instead of doing actual math to know how many extra rows/columns to generate to fill\n"
                                   "empty space in the image when the pattern is rotated, the script simply adds this many.\n"
                                   "If you scale the pattern down and/or rotate close to diagonal, it's possible the default\n"
                                   "won't be enough, in which case you can increase this.")
        self.slop_field.valueChanged.connect(self.updateImage)
        parm_layout.addRow('Slop', self.slop_field)

        # Background Color
        self.background_color_field = ColorParameter(QColor('#ffffff'))
        self.background_color_field.setToolTip('The background color, as hex or a named HTML color. '
                                               '(You can use transparent to leave the background transparent'
                                               ' if the image format supports transparency.)')
        self.background_color_field.valueChanged.connect(self.updateImage)
        parm_layout.addRow('Background', self.background_color_field)

        # Shape

        # Color Scheme

        # Node Fill Color
        self.node_fill_color_field = ColorParameter(QColor('#cccccc'))
        self.node_fill_color_field.setToolTip('The color to use to fill node shapes (as hex), or cycle to cycle through the color scheme'
                                              ' colors, or random to randomly choose a color scheme color, or none to not fill nodes.')
        self.node_fill_color_field.valueChanged.connect(self.updateImage)
        parm_layout.addRow('Node Fill', self.node_fill_color_field)

        # Node Stroke Color
        self.node_stroke_color_field = ColorParameter(QColor('#cccccc'))
        self.node_stroke_color_field.setToolTip('The color to use to draw node outlines (as hex), or cycle to cycle through the color scheme'
                                                ' colors, or random to randomly choose a color scheme color, or none to not draw node outlines.')
        self.node_stroke_color_field.valueChanged.connect(self.updateImage)
        parm_layout.addRow('Node Stroke', self.node_stroke_color_field)

        # Wire Style
        self.wire_style_combo = QComboBox()
        self.wire_style_combo.addItem('Bezier', 'bezier')
        self.wire_style_combo.addItem('Straight', 'straight')
        self.wire_style_combo.setToolTip('How to draw the "wires" connecting the nodes.')
        self.wire_style_combo.currentIndexChanged.connect(self.updateImage)
        parm_layout.addRow('Wire Style', self.wire_style_combo)

        # Wire Stroke Color
        self.wire_stroke_color_field = ColorParameter(QColor('#cccccc'))
        self.wire_stroke_color_field.setToolTip('The color to use to draw "wires" (as hex), or cycle to cycle through the color scheme'
                                                ' colors, or random to randomly choose a color scheme color, or none to not draw wires.')
        self.wire_stroke_color_field.valueChanged.connect(self.updateImage)
        parm_layout.addRow('Wire Stroke', self.wire_stroke_color_field)

        # Connector Fill Color
        self.connector_fill_color_field = ColorParameter(QColor('#ffffff'))
        self.connector_fill_color_field.setToolTip('The color to use to fill connectors (as hex), or cycle to cycle through the color scheme'
                                                   ' colors, or random to randomly choose a color scheme color.')
        self.connector_fill_color_field.valueChanged.connect(self.updateImage)
        parm_layout.addRow('Connector Fill', self.connector_fill_color_field)

        # Connector Stroke Color
        self.connector_stroke_color_field = ColorParameter(QColor('#cccccc'))
        self.connector_stroke_color_field.setToolTip('The color to use to draw connector outlines (as hex), or cycle to cycle through the color scheme'
                                                     ' colors, or random to randomly choose a color scheme color, or none to not draw connector outlines.')
        self.connector_stroke_color_field.valueChanged.connect(self.updateImage)
        parm_layout.addRow('Connector Stroke', self.connector_stroke_color_field)

        # Stroke Width
        self.stroke_width_field = NumParameter(2.0, (0, 10), 0.1)
        self.stroke_width_field.setToolTip('The width (in pixels) to draw node outlines.')
        self.stroke_width_field.valueChanged.connect(self.updateImage)
        parm_layout.addRow('Stroke Width', self.stroke_width_field)

        # Wire Width
        self.wire_width_field = NumParameter(2.0, (0, 10), 0.1)
        self.wire_width_field.setToolTip('The width (in pixels) to draw "wires".')
        self.wire_width_field.valueChanged.connect(self.updateImage)
        parm_layout.addRow('Wire Width', self.wire_width_field)

        # Saturation
        self.saturation_field = NumParameter(1.0, (0, 1), 0.05)
        self.saturation_field.setToolTip('These options let you set the saturation (as in the HSL color model) for the random hues.')
        self.saturation_field.valueChanged.connect(self.updateImage)
        parm_layout.addRow('Saturation', self.saturation_field)

        # Lightness
        self.lightness_field = NumParameter(0.5, (0, 1), 0.05)
        self.lightness_field.setToolTip('These options let you set the lightness (as in the HSL color model) for the random hues.')
        self.lightness_field.valueChanged.connect(self.updateImage)
        parm_layout.addRow('Lightness', self.lightness_field)

        # Seed
        self.seed_field = NumParameter(42, (0, 9999), 1)
        self.seed_field.setToolTip('Just a seed for the random.')
        self.seed_field.valueChanged.connect(self.updateImage)
        parm_layout.addRow('Seed', self.seed_field)

        spacer = QSpacerItem(0, 0, QSizePolicy.Ignored, QSizePolicy.Expanding)
        side_layout.addSpacerItem(spacer)

        # Output
        output_button = QPushButton('Output')
        output_button.clicked.connect(self.showOutputDialog)
        side_layout.addWidget(output_button)

        # Data
        self.__svg_data = None
        self.__image = None

        # Init
        self.updateImage()

    def generateImage(self):
        width = self.width_field.value()
        height = self.height_field.value()

        self.__svg_data = wallpaper.generate(width, height,
                                             scale=self.scale_field.value(),
                                             rotate=self.rotation_field.value(),
                                             slop=self.slop_field.value(),
                                             background=self.background_color_field.value(),
                                             nodestroke=self.node_stroke_color_field.value(),
                                             nodefill=self.node_fill_color_field.value(),
                                             wirestyle=self.wire_style_combo.currentData(Qt.UserRole),
                                             wirestroke=self.wire_stroke_color_field.value(),
                                             connfill=self.connector_fill_color_field.value(),
                                             connstroke=self.connector_stroke_color_field.value(),
                                             strokewidth=self.stroke_width_field.value(),
                                             wirewidth=self.wire_width_field.value(),
                                             saturation=self.saturation_field.value(),
                                             lightness=self.lightness_field.value(),
                                             seed=self.seed_field.value())
        renderer = QSvgRenderer(QByteArray(self.__svg_data.encode('utf8')))
        if not renderer.isValid():
            self.__svg_data = None
            raise Exception('Generated SVG is not valid')

        self.__image = QImage(width, height, QImage.Format_ARGB32)
        painter = QPainter()
        painter.begin(self.__image)
        painter.setRenderHints(QPainter.HighQualityAntialiasing)
        renderer.render(painter)
        painter.end()
        return self.__image

    def resizeEvent(self, event):
        self.view.setImage(self.__image)
        super(MainWindow, self).resizeEvent(event)

    def updateImage(self):
        self.view.setImage(self.generateImage())

    def showOutputDialog(self):
        if not self.__svg_data:
            return

        file_path, filters = QFileDialog.getSaveFileName(self, 'Output Image',
                                                         filter='Raster (*.png *.jpg);;Vector (*.svg)')
        if not file_path:
            return

        if file_path.endswith('.svg'):
            with open(file_path, 'w') as file:
                file.write(self.__svg_data)
        elif file_path.endswith(('.png', '.jpg')):
            self.__image.save(file_path)

        # Todo: save/load project files
        # Todo: save/load config files


if __name__ == '__main__':
    import os
    import sys

    try:
        import hou

        QCoreApplication.addLibraryPath(os.path.join(os.path.dirname(sys.executable), 'Qt_plugins'))
    except ImportError:
        pass

    app = QApplication([])
    # Todo: set parms from input args
    window = MainWindow()
    window.show()
    app.exec_()
