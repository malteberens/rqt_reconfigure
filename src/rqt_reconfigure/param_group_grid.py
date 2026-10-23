# Copyright (c) 2019 Open Source Robotics Foundation, Inc.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#    * Neither the name of the copyright holder nor the names of its
#      contributors may be used to endorse or promote products derived from
#      this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from python_qt_binding.QtCore import QMargins, Qt
from python_qt_binding.QtGui import QFont
from python_qt_binding.QtWidgets import (QFormLayout, QSizePolicy, QToolButton,
                                         QVBoxLayout, QWidget)


class _Group(QWidget):
    """Foldable section holding parameter rows and nested sub-groups."""

    def __init__(self, title, expanded, on_toggled):
        super().__init__()
        self._on_toggled = on_toggled

        outer = QVBoxLayout(self)
        outer.setContentsMargins(QMargins(0, 0, 0, 0))
        outer.setSpacing(0)

        self.header = QToolButton(self)
        self.header.setText(title)
        font = QFont(self.header.font())
        font.setBold(True)
        self.header.setFont(font)
        self.header.setCheckable(True)
        self.header.setAutoRaise(True)
        self.header.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        outer.addWidget(self.header)

        self.body = QWidget(self)
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(QMargins(16, 0, 0, 0))
        self.form = QFormLayout()
        self.body_layout.addLayout(self.form)
        outer.addWidget(self.body)

        self.header.toggled.connect(self._set_expanded)
        self.header.setChecked(expanded)
        self._set_expanded(expanded)

    def _set_expanded(self, expanded):
        self.header.setArrowType(
            Qt.ArrowType.DownArrow if expanded else Qt.ArrowType.RightArrow)
        self.body.setVisible(expanded)
        self._on_toggled(expanded)

    def is_empty(self):
        # The form layout itself is the only remaining item when nothing is left.
        return self.form.rowCount() == 0 and self.body_layout.count() == 1


class GroupedParamGrid(QVBoxLayout):
    """
    Drop-in replacement for the QFormLayout used by the parameter editors.

    Parameters are grouped into foldable sections by the dot-separated
    segments of their name (the YAML nesting); the row label shows only the
    last segment.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContentsMargins(QMargins(0, 0, 0, 0))
        self._root_form = QFormLayout()
        self.addLayout(self._root_form)
        self._groups = {}
        self._field_path = {}
        # Survives group removal so filtering doesn't reset folding.
        self._expanded = {}

    def addRow(self, label, field):
        *path, leaf = field.parameter.name.split('.')
        path = tuple(path)
        label.setText(leaf)
        self._form_for(path).addRow(label, field)
        self._field_path[field] = path

    def removeRow(self, field):
        path = self._field_path.pop(field, None)
        if path is None:
            return
        self._form_for(path).removeRow(field)
        while path and self._groups[path].is_empty():
            group = self._groups.pop(path)
            self._parent_layout(path).removeWidget(group)
            group.hide()
            group.deleteLater()
            path = path[:-1]

    def _parent_layout(self, path):
        return self if len(path) == 1 else self._groups[path[:-1]].body_layout

    def _form_for(self, path):
        for depth in range(1, len(path) + 1):
            key = path[:depth]
            if key not in self._groups:
                group = _Group(
                    key[-1], self._expanded.get(key, True),
                    lambda expanded, k=key: self._expanded.__setitem__(k, expanded))
                self._parent_layout(key).addWidget(group)
                self._groups[key] = group
        return self._groups[path].form if path else self._root_form
