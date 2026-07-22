# -*- coding: utf-8 -*-
"""
Instance Utility v1.0.1
=======================
A tool to detect and manage instances in a Maya scene.

Main features:
    - Automatic detection of Shape / Transform instances with a tree view
    - Reference count and depth display
    - Two-way sync between the list and the scene selection
    - Uninstance selected nodes (selection only / including descendants)
    - Duplicate as instance
    - Relink: make selected meshes share a picked source object's shape
    - Automatic outliner colorizing and bulk reset
    - English / Vietnamese UI toggle (English is the default)

Uninstance rules:
    - If a selected node has a shared Shape below it (e.g. Group1|pCube1):
        -> Uninstance the Shape (give it its own unique Shape)
        -> duplicate with instanceLeaf=False, then removeObject on the path
    - Otherwise, if the selected node itself is a Transform instance:
        -> Break only the Transform-instance relationship
        -> duplicate with instanceLeaf=True so shared child Shapes are kept
    - Neither case -> skip (warning only, colors preserved)

Relink rules:
    - Pick a source transform whose (first non-intermediate) mesh shape
      will be shared.
    - Each selected target transform is instanced onto that source shape,
      and its own shape is deleted, so they share one shape node.
    - Guards (optional): target must match the source in topology
      (vertex / edge / face counts) and in object-space pivot.

Colorizing rule:
    "Parents that share the same child get the same color."
    - Regardless of Shape/Transform type, the parent Transforms of a shared
      child node form one color group and are painted the same color.
    - If parent nodes overlap across multiple sharing relationships, the
      chained parent groups are unified into a single color.
    - The shared child node itself is not colored (only the parents are).

Depth column:
    How many generations of instancing are stacked on a node.
    - Simple Shape sharing = 1
    - One Transform-instance layer above it = 2
    - One more layer = 3

Supports: Maya 2023 / 2024 / 2025 / 2026
Qt:       PySide2 / PySide6

Usage:
    import instance_utility
    instance_utility.show()

Author: Pome3D
"""

import colorsys

import maya.cmds as cmds
import maya.OpenMaya as om
import maya.OpenMayaUI as omui

# ============================================================
# Qt 両対応のインポート
# ============================================================
try:
    from PySide6 import QtCore, QtGui, QtWidgets
    from shiboken6 import wrapInstance
    QT_VERSION = 6
except ImportError:
    from PySide2 import QtCore, QtGui, QtWidgets
    from shiboken2 import wrapInstance
    QT_VERSION = 2


# ============================================================
# 言語辞書
# ============================================================
def _detect_default_language():
    """
    Return the default UI language.

    English is the default. Vietnamese is only used if Maya itself
    reports a Vietnamese UI locale (rare), otherwise English wins.
    """
    try:
        ui_lang = cmds.about(uiLanguage=True) or ""
    except Exception:
        ui_lang = ""
    if ui_lang.lower().startswith("vi"):
        return "vi"
    return "en"


LANG = _detect_default_language()

TEXTS = {
    "en": {
        "window_title": "Instance Utility v1.0.1",
        "tool_description": "Detect and manage instances in the scene.",
        "group_list": "Instance List",
        "btn_refresh": "Refresh List",
        "tooltip_refresh": "Lists Shape Instances and Transform Instances in the scene. Press to update the list.",
        "group_action": "Actions",
        "group_convert": "Convert",
        "btn_uninstance": "Convert to\nObject",
        "tooltip_uninstance": "Converts selected instances (or all instances in the scene) to unique objects.",
        "radio_selected": "Selected",
        "radio_all": "All",
        "chk_recursive_uninst": "Also uninstance descendants",
        "group_duplicate": "Duplicate",
        "btn_create_instance": "Duplicate as\nInstance",
        "tooltip_duplicate": "Duplicates selected nodes as instances. Toggle auto-colorize with the checkbox.",
        "chk_auto_colorize": "Auto Colorize",
        "group_relink": "Relink",
        "btn_pick_source": "Pick Source",
        "tooltip_pick_source": "Pick the source object from the scene selection. Its shape will be shared by the relinked meshes.",
        "btn_relink": "Relink Selected\nto Source",
        "tooltip_relink": "Makes the selected meshes share the source object's shape node. Targets must match the source in topology (vertex / edge / face counts) and pivot, or they are skipped.",
        "relink_source_prefix": "Source: ",
        "relink_source_none": "(none)",
        "group_color": "Display",
        "btn_apply_color": "Colorize via Outliner Color",
        "tooltip_apply_color": "Colorizes instances via outliner colors. Nodes that share children are painted the same color.",
        "btn_clear_color": "Reset Outliner Colors",
        "tooltip_clear_color": "Resets all assigned outliner colors. Use before final submission.",
        "label_sync": "Sync List \u21c4 Scene Selection",
        "col_node": "Node",
        "col_type": "Type",
        "col_count": "Refs",
        "col_depth": "Depth",
        "shape_instance": "Shape",
        "transform_instance": "Transform",
        "status_ready": "Ready",
        "status_found": "Found: Shape {shape} / Transform {xform}",
        "status_none": "No instances found",
        "status_uninst_done": "Converted: {n} nodes",
        "status_color_applied": "Colors applied: {n} nodes",
        "status_color_cleared": "Colors cleared: {n} nodes",
        "status_created": "Duplicated: {n} nodes",
        "status_source_picked": "Source set: {name}",
        "status_relink_done": "Relinked: {n} nodes (skipped {s})",
        "warn_no_selection": "Nothing is selected",
        "warn_no_instance_selected": "Please select an instance",
        "warn_relink_no_source": "Pick a source object first",
        "warn_relink_source_gone": "Source object no longer exists. Pick it again.",
        "warn_relink_no_targets": "Select the target meshes to relink",
        "warn_relink_no_mesh": "Object has no usable mesh shape: {name}",
        "confirm_uninstance_all_title": "Confirm",
        "confirm_uninstance_all_msg": "Convert all instances in the scene to unique objects.\nProceed?",
    },
    "vi": {
        "window_title": "Instance Utility v1.0.1",
        "tool_description": "Ph\u00e1t hi\u1ec7n v\u00e0 qu\u1ea3n l\u00fd instance trong scene.",
        "group_list": "Danh s\u00e1ch Instance",
        "btn_refresh": "L\u00e0m m\u1edbi danh s\u00e1ch",
        "tooltip_refresh": "Li\u1ec7t k\u00ea Shape Instance v\u00e0 Transform Instance trong scene. Nh\u1ea5n \u0111\u1ec3 c\u1eadp nh\u1eadt danh s\u00e1ch.",
        "group_action": "Thao t\u00e1c",
        "group_convert": "Chuy\u1ec3n \u0111\u1ed5i",
        "btn_uninstance": "Chuy\u1ec3n th\u00e0nh\n\u0111\u1ed1i t\u01b0\u1ee3ng",
        "tooltip_uninstance": "Chuy\u1ec3n instance \u0111ang ch\u1ecdn (ho\u1eb7c to\u00e0n b\u1ed9 instance trong scene) th\u00e0nh \u0111\u1ed1i t\u01b0\u1ee3ng ri\u00eang bi\u1ec7t.",
        "radio_selected": "\u0110ang ch\u1ecdn",
        "radio_all": "To\u00e0n b\u1ed9",
        "chk_recursive_uninst": "G\u1ee1 c\u1ea3 instance c\u1ea5p d\u01b0\u1edbi",
        "group_duplicate": "Nh\u00e2n b\u1ea3n",
        "btn_create_instance": "Nh\u00e2n b\u1ea3n\nth\u00e0nh Instance",
        "tooltip_duplicate": "Nh\u00e2n b\u1ea3n c\u00e1c node \u0111ang ch\u1ecdn th\u00e0nh instance. B\u1eadt/t\u1eaft t\u1ef1 \u0111\u1ed9ng t\u00f4 m\u00e0u b\u1eb1ng \u00f4 ch\u1ecdn.",
        "chk_auto_colorize": "T\u1ef1 \u0111\u1ed9ng t\u00f4 m\u00e0u",
        "group_relink": "Li\u00ean k\u1ebft l\u1ea1i",
        "btn_pick_source": "Ch\u1ecdn ngu\u1ed3n",
        "tooltip_pick_source": "Ch\u1ecdn \u0111\u1ed1i t\u01b0\u1ee3ng ngu\u1ed3n t\u1eeb scene. Shape c\u1ee7a n\u00f3 s\u1ebd \u0111\u01b0\u1ee3c c\u00e1c mesh li\u00ean k\u1ebft d\u00f9ng chung.",
        "btn_relink": "Li\u00ean k\u1ebft\nv\u1ec1 ngu\u1ed3n",
        "tooltip_relink": "Cho c\u00e1c mesh \u0111ang ch\u1ecdn d\u00f9ng chung shape c\u1ee7a \u0111\u1ed1i t\u01b0\u1ee3ng ngu\u1ed3n. M\u1ee5c ti\u00eau ph\u1ea3i kh\u1edbp ngu\u1ed3n v\u1ec1 topology (s\u1ed1 \u0111\u1ec9nh / c\u1ea1nh / m\u1eb7t) v\u00e0 pivot, n\u1ebfu kh\u00f4ng s\u1ebd b\u1ecb b\u1ecf qua.",
        "relink_source_prefix": "Ngu\u1ed3n: ",
        "relink_source_none": "(ch\u01b0a ch\u1ecdn)",
        "group_color": "Hi\u1ec3n th\u1ecb",
        "btn_apply_color": "T\u00f4 m\u00e0u qua Outliner Color",
        "tooltip_apply_color": "T\u00f4 m\u00e0u instance b\u1eb1ng outliner color. C\u00e1c node d\u00f9ng chung con \u0111\u01b0\u1ee3c t\u00f4 c\u00f9ng m\u00e0u.",
        "btn_clear_color": "\u0110\u1eb7t l\u1ea1i Outliner Color",
        "tooltip_clear_color": "X\u00f3a to\u00e0n b\u1ed9 outliner color \u0111\u00e3 g\u00e1n. D\u00f9ng tr\u01b0\u1edbc khi n\u1ed9p b\u00e0i.",
        "label_sync": "\u0110\u1ed3ng b\u1ed9 Danh s\u00e1ch \u21c4 Scene",
        "col_node": "Node",
        "col_type": "Lo\u1ea1i",
        "col_count": "Tham chi\u1ebfu",
        "col_depth": "C\u1ea5p",
        "shape_instance": "Shape",
        "transform_instance": "Transform",
        "status_ready": "S\u1eb5n s\u00e0ng",
        "status_found": "T\u00ecm th\u1ea5y: Shape {shape} / Transform {xform}",
        "status_none": "Kh\u00f4ng t\u00ecm th\u1ea5y instance",
        "status_uninst_done": "\u0110\u00e3 chuy\u1ec3n \u0111\u1ed5i: {n} node",
        "status_color_applied": "\u0110\u00e3 t\u00f4 m\u00e0u: {n} node",
        "status_color_cleared": "\u0110\u00e3 x\u00f3a m\u00e0u: {n} node",
        "status_created": "\u0110\u00e3 nh\u00e2n b\u1ea3n: {n} node",
        "status_source_picked": "\u0110\u00e3 \u0111\u1eb7t ngu\u1ed3n: {name}",
        "status_relink_done": "\u0110\u00e3 li\u00ean k\u1ebft: {n} node (b\u1ecf qua {s})",
        "warn_no_selection": "Ch\u01b0a ch\u1ecdn g\u00ec",
        "warn_no_instance_selected": "H\u00e3y ch\u1ecdn m\u1ed9t instance",
        "warn_relink_no_source": "H\u00e3y ch\u1ecdn \u0111\u1ed1i t\u01b0\u1ee3ng ngu\u1ed3n tr\u01b0\u1edbc",
        "warn_relink_source_gone": "\u0110\u1ed1i t\u01b0\u1ee3ng ngu\u1ed3n kh\u00f4ng c\u00f2n t\u1ed3n t\u1ea1i. H\u00e3y ch\u1ecdn l\u1ea1i.",
        "warn_relink_no_targets": "H\u00e3y ch\u1ecdn c\u00e1c mesh m\u1ee5c ti\u00eau \u0111\u1ec3 li\u00ean k\u1ebft",
        "warn_relink_no_mesh": "\u0110\u1ed1i t\u01b0\u1ee3ng kh\u00f4ng c\u00f3 mesh shape d\u00f9ng \u0111\u01b0\u1ee3c: {name}",
        "confirm_uninstance_all_title": "X\u00e1c nh\u1eadn",
        "confirm_uninstance_all_msg": "Chuy\u1ec3n to\u00e0n b\u1ed9 instance trong scene th\u00e0nh \u0111\u1ed1i t\u01b0\u1ee3ng ri\u00eang bi\u1ec7t.\nTi\u1ebfp t\u1ee5c?",
    },
}


def tr(key, **kwargs):
    text = TEXTS.get(LANG, TEXTS["en"]).get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text


def _make_desc_label(text):
    label = QtWidgets.QLabel(text)
    label.setWordWrap(True)
    label.setStyleSheet("""
        QLabel {
            color: #aaaaaa;
            font-size: 8pt;
        }
    """)
    return label


# ============================================================
# 言語切替トグルウィジェット
# ============================================================
class LanguageToggle(QtWidgets.QWidget):
    """
    A toggle widget with a label on each side and a slide switch between.

        EN  [\u25cf\u2500\u2500]  VI      (English mode)
        EN  [\u2500\u2500\u25cf]  VI      (Vietnamese mode)

    Click anywhere on the widget to toggle.
    Emits toggled(bool)  (True = Vietnamese/right, False = English/left).
    """

    toggled = QtCore.Signal(bool)

    # スイッチ部分のサイズ
    SWITCH_W = 34
    SWITCH_H = 16
    KNOB_R = 6        # ノブの半径
    KNOB_MARGIN = 2   # トラック端とノブのマージン

    LABEL_COLOR_ACTIVE = QtGui.QColor(235, 235, 235)
    LABEL_COLOR_INACTIVE = QtGui.QColor(130, 130, 130)
    TRACK_COLOR_OFF = QtGui.QColor(70, 70, 70)    # 日本語側
    TRACK_COLOR_ON = QtGui.QColor(90, 120, 160)   # 英語側
    KNOB_COLOR = QtGui.QColor(230, 230, 230)
    BORDER_COLOR = QtGui.QColor(50, 50, 50)

    def __init__(self, left_label=u"EN", right_label=u"VI", parent=None):
        super(LanguageToggle, self).__init__(parent)
        self._left_label = left_label
        self._right_label = right_label
        self._checked = False  # False = English(left), True = Vietnamese(right)

        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setToolTip(u"Toggle language / \u0110\u1ed5i ng\u00f4n ng\u1eef")

        # サイズを固定
        # フォントメトリクスでラベル幅を計算
        fm = QtGui.QFontMetrics(self.font())
        self._left_w = fm.horizontalAdvance(self._left_label) \
            if hasattr(fm, "horizontalAdvance") else fm.width(self._left_label)
        self._right_w = fm.horizontalAdvance(self._right_label) \
            if hasattr(fm, "horizontalAdvance") else fm.width(self._right_label)

        total_w = self._left_w + 6 + self.SWITCH_W + 6 + self._right_w + 4
        total_h = max(self.SWITCH_H, fm.height()) + 4
        self.setFixedSize(total_w, total_h)

    def isChecked(self):
        return self._checked

    def setChecked(self, checked):
        checked = bool(checked)
        if self._checked == checked:
            return
        self._checked = checked
        self.update()
        self.toggled.emit(self._checked)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.setChecked(not self._checked)
        super(LanguageToggle, self).mousePressEvent(event)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        w, h = self.width(), self.height()
        fm = painter.fontMetrics()
        text_y = (h + fm.ascent() - fm.descent()) / 2

        # left label (EN)
        left_color = (self.LABEL_COLOR_ACTIVE if not self._checked
                      else self.LABEL_COLOR_INACTIVE)
        painter.setPen(left_color)
        painter.drawText(2, int(text_y), self._left_label)

        # 中央のスイッチトラック
        sw_x = self._left_w + 6
        sw_y = (h - self.SWITCH_H) // 2
        track_rect = QtCore.QRectF(sw_x, sw_y, self.SWITCH_W, self.SWITCH_H)

        track_color = (self.TRACK_COLOR_ON if self._checked
                       else self.TRACK_COLOR_OFF)
        painter.setPen(QtGui.QPen(self.BORDER_COLOR, 1))
        painter.setBrush(QtGui.QBrush(track_color))
        painter.drawRoundedRect(
            track_rect, self.SWITCH_H / 2.0, self.SWITCH_H / 2.0)

        # ノブ
        knob_d = self.KNOB_R * 2
        if self._checked:
            # 右寄せ
            knob_x = sw_x + self.SWITCH_W - knob_d - self.KNOB_MARGIN
        else:
            # 左寄せ
            knob_x = sw_x + self.KNOB_MARGIN
        knob_y = sw_y + (self.SWITCH_H - knob_d) / 2.0
        painter.setPen(QtGui.QPen(self.BORDER_COLOR, 1))
        painter.setBrush(QtGui.QBrush(self.KNOB_COLOR))
        painter.drawEllipse(
            QtCore.QRectF(knob_x, knob_y, knob_d, knob_d))

        # right label (VI)
        right_color = (self.LABEL_COLOR_ACTIVE if self._checked
                       else self.LABEL_COLOR_INACTIVE)
        painter.setPen(right_color)
        right_x = sw_x + self.SWITCH_W + 6
        painter.drawText(int(right_x), int(text_y), self._right_label)

        painter.end()


# ============================================================
# Maya メインウィンドウ取得
# ============================================================
def get_maya_main_window():
    main_win_ptr = omui.MQtUtil.mainWindow()
    if main_win_ptr is None:
        return None
    return wrapInstance(int(main_win_ptr), QtWidgets.QWidget)


# ============================================================
# アウトライナ強制リフレッシュ
# ============================================================
def force_outliner_refresh():
    try:
        current_sel = cmds.ls(sl=True, long=True) or []
        cmds.refresh(force=True)
        try:
            panels = cmds.getPanel(type="outlinerPanel") or []
            for panel in panels:
                editor = cmds.outlinerPanel(panel, query=True, outlinerEditor=True)
                if editor:
                    cmds.outlinerEditor(editor, edit=True, refresh=True)
        except Exception:
            pass
        cmds.select(clear=True)
        if current_sel:
            existing = [n for n in current_sel if cmds.objExists(n)]
            if existing:
                cmds.select(existing, replace=True, noExpand=True)
        cmds.refresh()
    except Exception as e:
        om.MGlobal.displayWarning(u"アウトライナリフレッシュ失敗: {0}".format(e))


# ============================================================
# インスタンス検出ロジック
# ============================================================
class InstanceDetector(object):
    TYPE_SHAPE = "shape"
    TYPE_TRANSFORM = "transform"

    @classmethod
    def collect(cls):
        result = {cls.TYPE_SHAPE: [], cls.TYPE_TRANSFORM: []}

        shape_nodes = cmds.ls(shapes=True, long=True) or []
        for shape in shape_nodes:
            parents = cmds.listRelatives(shape, allParents=True, fullPath=True) or []
            if len(parents) >= 2:
                result[cls.TYPE_SHAPE].append((shape, sorted(parents)))

        transform_nodes = cmds.ls(type="transform", long=True) or []
        for xform in transform_nodes:
            parents = cmds.listRelatives(xform, allParents=True, fullPath=True) or []
            if len(parents) >= 2:
                result[cls.TYPE_TRANSFORM].append((xform, sorted(parents)))

        result[cls.TYPE_SHAPE].sort(key=lambda x: -len(x[1]))
        result[cls.TYPE_TRANSFORM].sort(key=lambda x: -len(x[1]))

        return result

    @staticmethod
    def compute_depth(node_path):
        """
        そのノードを起点に、配下にインスタンス関係が何階層連鎖しているかを返す。
        定義:
            - このノード自身がインスタンス関係の最も浅い起点(=shape共有の親Transform or
              transform共有の本体)として扱う
            - このノードの「下」を辿って、インスタンス関係が追加で何層あるかを数え上げる
        簡便な仕様:
            - このノードの直下子孫（DAG Descendants）を走査
            - 子孫のうち「複数親を持つShapeまたはTransform」が見つかれば、
              その子孫自身がさらにインスタンス起点となる → 深さ +1
            - それを再帰的に辿る
        戻り値: 1以上の整数
        """
        if not cmds.objExists(node_path):
            return 1

        def _max_depth_below(path, visited):
            """pathの配下(子孫)に潜むインスタンス起点のうち、最大の再帰深度を返す"""
            if path in visited:
                return 0
            visited.add(path)

            max_child_depth = 0
            children = cmds.listRelatives(path, children=True, fullPath=True) or []
            for c in children:
                # cがインスタンス起点かどうか判定
                # インスタンス起点 = 親が2つ以上ある(Shape/Transform問わず)
                try:
                    c_parents = cmds.listRelatives(c, allParents=True, fullPath=True) or []
                except Exception:
                    c_parents = []

                if len(c_parents) >= 2:
                    # ここが起点 → 自分(c)の下をさらに再帰
                    sub = _max_depth_below(c, visited)
                    # c自体をカウントするので +1
                    depth = 1 + sub
                    if depth > max_child_depth:
                        max_child_depth = depth
                else:
                    # cは起点ではないが、さらに下にあるかもしれないので再帰継続
                    sub = _max_depth_below(c, visited)
                    if sub > max_child_depth:
                        max_child_depth = sub
            return max_child_depth

        # 自分自身が1階層目、そこから下の最大階層を足す
        below = _max_depth_below(node_path, set())
        return 1 + below


# ============================================================
# インスタンス操作
# ============================================================
class InstanceOperator(object):

    _SHAPE_TYPES = ("mesh", "nurbsCurve", "nurbsSurface", "locator", "camera",
                    "subdiv", "bezierCurve", "lattice")

    @classmethod
    def uninstance_nodes(cls, nodes, recursive=False):
        """
        選択ノードが持つインスタンス関係を解除する。

        判定順 (Shape優先):
            1. 配下にShape共有のShapeがある
                → Shapeインスタンス解除モード (独自Shape化)
            2. 自身がTransformインスタンス
                → Transformインスタンス関係のみ解除
            3. どちらでもない → スキップ (warning)

        recursive=True のとき:
            選択ノード自身を処理した後、さらに各選択ノードの子孫に存在する
            すべてのインスタンス(Shape/Transform)を検出して個別に解除する。
            子孫のShapeインスタンスから先に処理し、次に残った
            Transformインスタンスを処理する。

        戻り値: 処理成功したノード数
        """
        if not nodes:
            return 0

        count = 0
        # 元の選択ノード(ルート)を記録。recursive時にこれらの配下を走査する
        root_nodes = list(nodes)

        # Step 1: 選択ノード自身を処理 (既存ロジックそのまま)
        for node in root_nodes:
            if not cmds.objExists(node):
                continue
            try:
                if cls._instance_to_object_single(node):
                    count += 1
            except Exception as e:
                om.MGlobal.displayWarning(
                    u"変換失敗: {0} ({1})".format(node, e)
                )

        # Step 2: recursive=True なら子孫のインスタンスも処理
        if recursive:
            # ルートはduplicateで名前やパスが変わっている可能性があるため、
            # 短縮名から現在のフルパスを再取得する
            current_roots = []
            for rn in root_nodes:
                short = rn.rsplit("|", 1)[-1]
                # 短縮名でlookupして、生きているパスを候補にする
                found = cmds.ls(short, long=True) or []
                current_roots.extend(found)
            current_roots = list(dict.fromkeys(current_roots))

            # Shape → Transform の順で処理
            # 処理1巡ごとに子孫を再収集することで、パス変更に対応
            count += cls._recursive_uninstance_under(current_roots)

        return count

    @classmethod
    def _recursive_uninstance_under(cls, root_paths):
        """
        指定ルート配下の全インスタンスを解除する。
        Shape共有 → Transform共有 の順で処理。
        各処理で _instance_to_object_single を呼ぶ。
        """
        count = 0

        # ---- フェーズ1: 配下の Shapeインスタンス を解除 ----
        safety = 5000
        while safety > 0:
            shape_targets = cls._collect_descendant_shape_instances(root_paths)
            if not shape_targets:
                break
            # 1件ずつ処理 (処理後にパスが変わる可能性があるので毎回再収集)
            target = shape_targets[0]
            if not cmds.objExists(target):
                safety -= 1
                continue
            try:
                if cls._instance_to_object_single(target):
                    count += 1
            except Exception as e:
                om.MGlobal.displayWarning(
                    u"変換失敗: {0} ({1})".format(target, e)
                )
                break
            safety -= 1

        # ---- フェーズ2: 配下の Transformインスタンス を解除 ----
        safety = 5000
        while safety > 0:
            xform_targets = cls._collect_descendant_transform_instances(
                root_paths)
            if not xform_targets:
                break
            target = xform_targets[0]
            if not cmds.objExists(target):
                safety -= 1
                continue
            try:
                if cls._instance_to_object_single(target):
                    count += 1
            except Exception as e:
                om.MGlobal.displayWarning(
                    u"変換失敗: {0} ({1})".format(target, e)
                )
                break
            safety -= 1

        return count

    @staticmethod
    def _collect_descendant_shape_instances(root_paths):
        """
        各ルート配下の「Shape共有の親Transform」のリストを返す。
        (Shape自体ではなく、Shape解除処理の対象である親Transformを返す)
        """
        result = []
        seen = set()
        for root in root_paths:
            if not cmds.objExists(root):
                continue
            # ルート自身も対象に含める (ルート直下のShape共有用)
            candidates = [root]
            descendants = cmds.listRelatives(
                root, allDescendents=True, fullPath=True) or []
            candidates.extend(descendants)

            for n in candidates:
                if not cmds.objExists(n):
                    continue
                if cmds.objectType(n, isAType="shape"):
                    continue
                # 直下のShape共有をチェック
                shapes = cmds.listRelatives(
                    n, shapes=True, fullPath=True) or []
                has_instance_shape = False
                for sh in shapes:
                    try:
                        sh_parents = cmds.listRelatives(
                            sh, allParents=True, fullPath=True) or []
                        if len(sh_parents) >= 2:
                            has_instance_shape = True
                            break
                    except Exception:
                        continue
                if has_instance_shape and n not in seen:
                    result.append(n)
                    seen.add(n)
        return result

    @staticmethod
    def _collect_descendant_transform_instances(root_paths):
        """
        各ルート配下の「Transformインスタンス」のリストを返す。
        子Transform共有での判定も行う (_is_transform_instance と同じ発想)。
        """
        result = []
        seen = set()

        for root in root_paths:
            if not cmds.objExists(root):
                continue
            # ルート自身も対象に含める
            candidates = [root]
            descendants = cmds.listRelatives(
                root, allDescendents=True, fullPath=True) or []
            candidates.extend(descendants)

            for n in candidates:
                if not cmds.objExists(n):
                    continue
                if cmds.objectType(n, isAType="shape"):
                    continue
                if n in seen:
                    continue

                # Transformインスタンス判定 (3段階チェック)
                is_inst = False
                parents = cmds.listRelatives(
                    n, allParents=True, fullPath=True) or []
                if len(parents) >= 2:
                    is_inst = True
                else:
                    try:
                        sel = om.MSelectionList()
                        sel.add(n)
                        dag = om.MDagPath()
                        sel.getDagPath(0, dag)
                        if dag.isInstanced():
                            is_inst = True
                    except Exception:
                        pass
                    if not is_inst:
                        # 配下に複数親ノードがあるか
                        sub = cmds.listRelatives(
                            n, allDescendents=True, fullPath=True) or []
                        for d in sub:
                            try:
                                d_parents = cmds.listRelatives(
                                    d, allParents=True, fullPath=True) or []
                                if len(d_parents) >= 2:
                                    is_inst = True
                                    break
                            except Exception:
                                continue

                if is_inst:
                    result.append(n)
                    seen.add(n)
        return result

    @classmethod
    def _instance_to_object_single(cls, node):
        """
        単一ノードのインスタンス関係を解除する。

        判定ロジック (Shape優先):
            1. Shape選択 → 親Transformに置き換え (以降、node は Transform)
            2. 配下にShape共有のShapeがあるか?
               → YES なら Shapeインスタンス解除モード (Amaterasu方式)
               → NO なら次へ
            3. 自身がTransformインスタンスか?
               → YES なら Transformインスタンス解除モード (専用処理)
               → NO ならスキップ

        戻り値: True = 成功、False = 対象外でスキップ
        """
        if not cmds.objExists(node):
            return False

        # Shape → 親Transform に置き換え
        if cmds.objectType(node, isAType="shape"):
            parents = cmds.listRelatives(node, parent=True,
                                         fullPath=True) or []
            if not parents:
                return False
            node = parents[0]

        # Shape優先判定
        if cls._has_child_shape_instance(node):
            # Shape解除モード: 従来のAmaterasu方式
            return cls._uninstance_shape_mode(node)
        elif cls._is_transform_instance(node):
            # Transform解除モード: 専用処理
            return cls._uninstance_transform_mode(node)
        else:
            # インスタンス関係なし → スキップ
            om.MGlobal.displayWarning(
                u"インスタンスではないためスキップ: {0}".format(node)
            )
            return False

    @staticmethod
    def _uninstance_shape_mode(node):
        """
        Shapeインスタンス解除モード (Amaterasu方式)。
        配下のShapeを独自化する。
        """
        short_name = node.rsplit("|", 1)[-1]

        try:
            new_node = cmds.duplicate(
                node, returnRootsOnly=True, instanceLeaf=False)
        except TypeError:
            new_node = cmds.duplicate(node, returnRootsOnly=True)
        if not new_node:
            return False
        new_node = new_node[0]

        # 元のインスタンス参照を削除
        try:
            if cmds.objectType(node, isAType="shape"):
                cmds.parent(node, removeObject=True, shape=True)
            else:
                cmds.parent(node, removeObject=True)
        except Exception as e:
            om.MGlobal.displayWarning(
                u"インスタンス参照削除失敗: {0} ({1})".format(node, e)
            )

        try:
            cmds.rename(new_node, short_name)
        except Exception:
            pass

        return True

    @classmethod
    def _uninstance_transform_mode(cls, node):
        """
        Transformインスタンス解除モード。
        選択ノード (そのフルパス) だけをインスタンス関係から離脱させる。
        配下のShape共有は維持 (instanceLeaf=True)。

        手順:
            1. 選択ノード (例: |group1) の親フルパスを記録
            2. cmds.duplicate(node, instanceLeaf=True) で独立複製を作る
            3. 複製結果が正しい親の下にない場合は cmds.parent で移動
               (既に正しい親配下にあるならスキップ。"already a child" warning回避)
            4. cmds.parent(node, removeObject=True) で元のインスタンス参照を削除
               → 指定フルパスのみ切断、共有相手 (|group2) は残る
            5. 複製ノードを元の短縮名にrename
        """
        short_name = node.rsplit("|", 1)[-1]

        # 元の親フルパス (Noneならワールド直下)
        orig_parents = cmds.listRelatives(node, parent=True,
                                          fullPath=True) or []
        target_parent = orig_parents[0] if orig_parents else None

        # 複製 (配下のShape共有は維持)
        try:
            new_node = cmds.duplicate(
                node, returnRootsOnly=True, instanceLeaf=True)
        except TypeError:
            new_node = cmds.duplicate(node, returnRootsOnly=True)
        if not new_node:
            return False
        new_full = cmds.ls(new_node[0], long=True)
        new_full = new_full[0] if new_full else new_node[0]

        # 複製結果を元の親の下に配置
        # 既に正しい親配下にあるならスキップ
        try:
            cur_parents = cmds.listRelatives(new_full, parent=True,
                                             fullPath=True) or []
            cur_parent = cur_parents[0] if cur_parents else None

            if target_parent and cmds.objExists(target_parent):
                if cur_parent != target_parent:
                    moved = cmds.parent(new_full, target_parent)
                    if moved:
                        new_full = cmds.ls(moved[0], long=True)[0]
            else:
                # ワールド直下に配置。既にワールド直下ならスキップ
                if cur_parent is not None:
                    moved = cmds.parent(new_full, world=True)
                    if moved:
                        new_full = cmds.ls(moved[0], long=True)[0]
        except Exception as e:
            om.MGlobal.displayWarning(
                u"親への移動失敗: {0} ({1})".format(new_full, e)
            )

        # 元のインスタンス参照 (選択したフルパス) を削除
        # これにより選択ノードだけがインスタンス関係から離脱する
        try:
            cmds.parent(node, removeObject=True)
        except Exception as e:
            om.MGlobal.displayWarning(
                u"インスタンス参照削除失敗: {0} ({1})".format(node, e)
            )

        # リネーム (元の短縮名に戻す)
        try:
            cmds.rename(new_full, short_name)
        except Exception:
            pass

        return True

    @staticmethod
    def _is_transform_instance(node_path):
        """
        そのTransformがTransformインスタンス関係を持っているかを判定。

        判定方法 (複数の手法で確実に拾う):
            1. listRelatives(allParents=True) で複数親 → Transformインスタンス
            2. OpenMaya の MDagPath.isInstanced() で判定
            3. 配下にTransformインスタンス(allParents>=2のTransform)が含まれているか
               → 自身がインスタンスなら、その配下のノードも別パスで参照されるため
                 子Transformの allParents が複数返ることで間接的に判定できる。
                 特にワールド直下のTransformインスタンス等、1, 2で拾えない
                 ケースを補完する。

        注意: この関数は「Shape共有優先判定」の後に呼ばれる前提。
              つまり配下のShape共有は既に別モードで処理されるので、
              ここで「子Transform共有」として検出されるのは純粋な
              Transformインスタンス関係のみ。
        """
        if not cmds.objExists(node_path):
            return False
        if cmds.objectType(node_path, isAType="shape"):
            return False

        # 判定1: 直接の親チェック
        parents = cmds.listRelatives(node_path, allParents=True,
                                     fullPath=True) or []
        if len(parents) >= 2:
            return True

        # 判定2: OpenMaya の isInstanced
        try:
            sel = om.MSelectionList()
            sel.add(node_path)
            dag = om.MDagPath()
            sel.getDagPath(0, dag)
            if dag.isInstanced():
                return True
        except Exception:
            pass

        # 判定3: 配下にインスタンス関係のノードがあるか
        # 自身がTransformインスタンスなら、配下のノードも複数パスで参照される
        try:
            descendants = cmds.listRelatives(node_path, allDescendents=True,
                                             fullPath=True) or []
        except Exception:
            descendants = []
        for d in descendants:
            try:
                d_parents = cmds.listRelatives(d, allParents=True,
                                               fullPath=True) or []
            except Exception:
                continue
            if len(d_parents) >= 2:
                # 配下にインスタンス関係のノードがある
                # = 自身が(または先祖が)Transformインスタンス関係にある
                return True

        return False

    @staticmethod
    def _has_child_shape_instance(node_path):
        """
        そのTransformの直下の子Shapeのいずれかが
        Shapeインスタンス(複数親を持つ)かどうか。

        intermediateObject フラグが立っているShape (履歴用の中間Shape) は
        通常のジオメトリではないため、判定上は除外する。
        Shape自体ではなく allDescendents=True 相当も併せてチェックすることで、
        より複雑な構造のプリミティブ (pCylinder等で複数Shapeを持つ場合) でも
        正しく検出できる。
        """
        if not cmds.objExists(node_path):
            return False

        # 直下のShape群を取得
        # noIntermediate=True で intermediateObject を除外
        shapes = cmds.listRelatives(node_path, shapes=True,
                                    fullPath=True,
                                    noIntermediate=True) or []

        # noIntermediate オプションが効かない環境への保険として、
        # 取得後にも intermediateObject 属性で再フィルタ
        filtered_shapes = []
        for sh in shapes:
            try:
                if cmds.attributeQuery("intermediateObject",
                                       node=sh, exists=True):
                    if cmds.getAttr("{0}.intermediateObject".format(sh)):
                        continue
                filtered_shapes.append(sh)
            except Exception:
                filtered_shapes.append(sh)

        for sh in filtered_shapes:
            try:
                sh_parents = cmds.listRelatives(sh, allParents=True,
                                                fullPath=True) or []
                if len(sh_parents) >= 2:
                    return True
            except Exception:
                continue
        return False

    @classmethod
    def uninstance_all(cls):
        """
        シーン内の全インスタンスをオブジェクトに変換する。

        アルゴリズム (提供された参考スクリプトをベースに実装):
            OpenMaya の MItDag で DAG を走査し、インスタンス化されている
            ノードのフルパス一覧を取得。
            1件取り出して、その親を duplicate + delete でインスタンス解除。
            全インスタンスが消えるまでループ。

        ノード指定は必ずフルパス (ロングネーム) で行う。
        同名ノードが複数存在する場合の "More than one object matches name"
        エラーを回避するため。

        戻り値: 処理回数
        """
        count = 0
        safety = 10000
        while safety > 0:
            instances = cls._get_all_instanced_paths()
            if not instances:
                break

            try:
                # fullPath=True で必ずロングネームを取得
                parent = cmds.listRelatives(
                    instances[0], parent=True, fullPath=True) or []
                if not parent:
                    safety -= 1
                    continue
                # parent[0] はロングネームなので duplicate/delete に
                # 安全に渡せる
                cmds.duplicate(parent[0], renameChildren=True)
                cmds.delete(parent[0])
                count += 1
            except Exception as e:
                om.MGlobal.displayWarning(
                    u"変換失敗: {0} ({1})".format(instances[0], e)
                )
                break

            safety -= 1

        return count

    @staticmethod
    def _get_all_instanced_paths():
        """
        DAG全体を走査して、インスタンス化されているノードの
        fullPathName のリストを返す (参考スクリプトの getInstances 相当)。
        """
        instances = []
        try:
            it = om.MItDag(om.MItDag.kBreadthFirst)
            while not it.isDone():
                if om.MItDag.isInstanced(it):
                    instances.append(it.fullPathName())
                it.next()
        except Exception as e:
            om.MGlobal.displayWarning(
                u"インスタンス列挙失敗: {0}".format(e)
            )
        return instances

    @staticmethod
    def create_instance_from_selection():
        sel = cmds.ls(sl=True, long=True) or []
        if not sel:
            return [], []
        new_nodes = cmds.instance(sel)
        cmds.select(new_nodes, replace=True)
        return new_nodes, sel

    # ----------------------------------------------------------------
    # Relink (share a source object's shape)
    # ----------------------------------------------------------------
    PIVOT_TOLERANCE = 1e-4

    @staticmethod
    def first_geo_shape(transform):
        """
        Return the first non-intermediate mesh shape (full path) under the
        given transform, or None. Intermediate (history) shapes are ignored.
        """
        if not transform or not cmds.objExists(transform):
            return None
        # If a shape was passed directly, resolve to its transform first.
        if cmds.objectType(transform, isAType="shape"):
            parents = cmds.listRelatives(transform, parent=True,
                                         fullPath=True) or []
            if not parents:
                return None
            transform = parents[0]

        shapes = cmds.listRelatives(transform, shapes=True, fullPath=True,
                                    type="mesh", noIntermediate=True) or []
        for sh in shapes:
            try:
                if cmds.attributeQuery("intermediateObject",
                                       node=sh, exists=True) and \
                        cmds.getAttr("{0}.intermediateObject".format(sh)):
                    continue
            except Exception:
                pass
            return sh
        return None

    @staticmethod
    def _mesh_topo_signature(shape):
        """Return (vtx, edge, face) counts for a mesh shape, or None."""
        try:
            v = cmds.polyEvaluate(shape, vertex=True)
            e = cmds.polyEvaluate(shape, edge=True)
            f = cmds.polyEvaluate(shape, face=True)
        except Exception:
            return None
        # polyEvaluate returns ints for these flags; guard against odd returns.
        if not all(isinstance(x, int) for x in (v, e, f)):
            return None
        return (v, e, f)

    @staticmethod
    def _object_pivots(transform):
        """Return (rotatePivot, scalePivot) in object space as tuples."""
        rp = cmds.xform(transform, query=True, objectSpace=True,
                        rotatePivot=True)
        sp = cmds.xform(transform, query=True, objectSpace=True,
                        scalePivot=True)
        return (tuple(rp), tuple(sp))

    @classmethod
    def _pivots_match(cls, transform_a, transform_b):
        try:
            rp_a, sp_a = cls._object_pivots(transform_a)
            rp_b, sp_b = cls._object_pivots(transform_b)
        except Exception:
            return False
        tol = cls.PIVOT_TOLERANCE
        for a, b in zip(rp_a + sp_a, rp_b + sp_b):
            if abs(a - b) > tol:
                return False
        return True

    @classmethod
    def relink_to_source(cls, source_transform, target_transforms,
                         check_topology=True, check_pivot=True):
        """
        Make each target transform share the source transform's shape node,
        so they become shape-instances of the source. The target's own
        shape(s) are removed.

        Per-target guards (only applied when the flag is True):
            - topology: vertex / edge / face counts must match the source
            - pivot:    object-space rotate & scale pivots must match

        A target that fails a guard is skipped (not force-linked).

        Returns: (relinked_count, skipped)
            skipped = [(target_path, reason), ...]
            reason in {"no_mesh", "no_topology", "topology_mismatch",
                       "pivot_mismatch", "same_shape", "error"}
        """
        skipped = []

        src_shape = cls.first_geo_shape(source_transform)
        if src_shape is None:
            # Nothing to share -> every target is skipped.
            return 0, [(t, "no_mesh") for t in target_transforms]

        src_sig = cls._mesh_topo_signature(src_shape) if check_topology else None

        relinked = 0
        for tgt in target_transforms:
            if not tgt or not cmds.objExists(tgt):
                continue
            if tgt == source_transform:
                continue

            tgt_shape = cls.first_geo_shape(tgt)
            if tgt_shape is None:
                skipped.append((tgt, "no_mesh"))
                continue

            # Already sharing this exact shape node?
            if cmds.objExists(src_shape) and cmds.objExists(tgt_shape):
                if cmds.ls(src_shape, uuid=True) == cmds.ls(tgt_shape, uuid=True):
                    skipped.append((tgt, "same_shape"))
                    continue

            # Topology guard
            if check_topology:
                tgt_sig = cls._mesh_topo_signature(tgt_shape)
                if tgt_sig is None or src_sig is None:
                    skipped.append((tgt, "no_topology"))
                    continue
                if tgt_sig != src_sig:
                    skipped.append((tgt, "topology_mismatch"))
                    continue

            # Pivot guard
            if check_pivot and not cls._pivots_match(source_transform, tgt):
                skipped.append((tgt, "pivot_mismatch"))
                continue

            # Perform the relink:
            #   1. Instance the source shape under the target transform.
            #   2. Delete the target's own original shape(s).
            try:
                # Capture the target's existing shapes (incl. intermediates)
                # before we add the shared one, so we can delete exactly those.
                orig_shapes = cmds.listRelatives(
                    tgt, shapes=True, fullPath=True) or []

                cmds.parent(src_shape, tgt,
                            shape=True, addObject=True, relative=True)

                for sh in orig_shapes:
                    if cmds.objExists(sh):
                        cmds.delete(sh)

                relinked += 1
            except Exception as e:
                om.MGlobal.displayWarning(
                    u"Relink failed: {0} ({1})".format(tgt, e))
                skipped.append((tgt, "error"))

        return relinked, skipped


# ============================================================
# アウトライナカラー管理
# ============================================================
class OutlinerColorizer(object):
    """
    色分けルール:
        「同じ子を共有している親同士を同じ色にする」

        Shape/Transformの種別は問わず、allParentsが2つ以上あるノード
        （= 共有されている子）ごとに、その親群を1つの「色グループ」として扱う。

        異なる子に由来する親グループであっても、親ノードが重複していれば
        同じ色グループに併合する（Union-Find）。これにより、多階層インスタンス
        でも「子を共有している親同士」が連鎖的に同色で統一される。

        例:
            Group1 / Group2 が pCube1, pCube2 (Transformインスタンス) を共有
                → Group1, Group2 は同色 (例: 青)
            pCube1 / pCube2 (Group1配下・Group2配下の計4ノード) が
            pCubeShape1 を共有
                → pCube1(G1), pCube2(G1), pCube1(G2), pCube2(G2) は同色 (例: 赤)

        色を付ける対象は「親Transform群」のみで、共有されているShape/Transform
        本体自体には色を付けない (Transform本体に色を付けるとパス表示が紛らわしい
        ため、親側のみに着色する方針)。
    """

    S_DEFAULT = 0.50
    V_DEFAULT = 0.95

    @classmethod
    def _hsv_colors(cls, count, saturation=None, value=None):
        if count <= 0:
            return []
        s = cls.S_DEFAULT if saturation is None else saturation
        v = cls.V_DEFAULT if value is None else value
        colors = []
        for i in range(count):
            h = (i / float(count)) if count > 1 else 0.0
            r, g, b = colorsys.hsv_to_rgb(h, s, v)
            colors.append((r, g, b))
        return colors

    @classmethod
    def _build_parent_groups(cls, instance_data):
        """
        instance_data から「親ノードの色グループ」をUnion-Findで構築する。

        処理:
            - Shape共有 / Transform共有 いずれも "共有されている子" の allParents を
              ひとつの集合として扱う
            - それらの集合間で親ノードが重複していれば同じ色グループに併合する

        戻り値: [set(parent_path, ...), ...]  各集合が1つの色グループ
        """
        shape_list = instance_data.get(InstanceDetector.TYPE_SHAPE, [])
        xform_list = instance_data.get(InstanceDetector.TYPE_TRANSFORM, [])

        # 各「共有されている子」の親集合 (重複除去)
        parent_sets = []
        for _child, parents in shape_list:
            if len(parents) >= 2:
                parent_sets.append(set(parents))
        for _child, parents in xform_list:
            if len(parents) >= 2:
                parent_sets.append(set(parents))

        if not parent_sets:
            return []

        # Union-Find
        # 親ノード → グループID のマップを管理し、共通する親があれば併合
        parent_to_group = {}  # parent_path -> group_id(int)
        groups = {}           # group_id -> set(parent_path)
        next_group_id = [0]

        def new_group(nodes):
            gid = next_group_id[0]
            next_group_id[0] += 1
            groups[gid] = set(nodes)
            for n in nodes:
                parent_to_group[n] = gid
            return gid

        def merge_groups(gid_a, gid_b):
            if gid_a == gid_b:
                return gid_a
            # 小さい方を大きい方に吸収 (gid_a を残す)
            merged = groups[gid_a] | groups[gid_b]
            groups[gid_a] = merged
            for n in groups[gid_b]:
                parent_to_group[n] = gid_a
            del groups[gid_b]
            return gid_a

        for p_set in parent_sets:
            existing_gids = set()
            for p in p_set:
                if p in parent_to_group:
                    existing_gids.add(parent_to_group[p])

            if not existing_gids:
                # 新規グループ
                new_group(p_set)
            else:
                # 既存グループのいずれかに属している親がいる
                # → まず既存グループを1つに統合
                gid_list = list(existing_gids)
                base_gid = gid_list[0]
                for other_gid in gid_list[1:]:
                    base_gid = merge_groups(base_gid, other_gid)
                # → 今回の親集合のうち未所属のものを追加
                for p in p_set:
                    if p not in parent_to_group:
                        groups[base_gid].add(p)
                        parent_to_group[p] = base_gid

        # group_idの順序を安定化させるため、各グループの最小パスでソート
        group_list = list(groups.values())
        group_list.sort(key=lambda s: min(s))
        return group_list

    @classmethod
    def apply(cls, instance_data, inherit_color_map=None):
        """
        戻り値: (適用数, final_color_map)
            final_color_map = {node_path: (r, g, b)}

        inherit_color_map:
            {node_path: (r, g, b)} を渡すと、各色グループに対して
            「グループ内のいずれかのノードがこのマップに登録されていれば
            その色をグループの代表色として引き継ぐ」処理を行う。
            これにより、変換実行後に色を再設定する際、変換前と同じ
            グループには同じ色を維持できる。
        """
        parent_groups = cls._build_parent_groups(instance_data)

        # 各グループに対する代表色を決定する
        # 引き継ぎマップに該当ノードがあればその色を使う、
        # なければ後で新色を割り当てる
        group_inherit_color = [None] * len(parent_groups)
        if inherit_color_map:
            for i, group in enumerate(parent_groups):
                for p in group:
                    if p in inherit_color_map:
                        group_inherit_color[i] = inherit_color_map[p]
                        break

        # 引き継げないグループ (新規) のために色相を均等分割した色を用意
        new_color_indices = [
            i for i, c in enumerate(group_inherit_color) if c is None
        ]
        new_colors = cls._hsv_colors(len(new_color_indices))
        for j, gi in enumerate(new_color_indices):
            group_inherit_color[gi] = new_colors[j]

        touched_nodes = set()
        count = 0

        for idx, group in enumerate(parent_groups):
            color = group_inherit_color[idx]
            for p in group:
                cls._set_color(p, color)
                touched_nodes.add(p)
                count += 1

        # 最終色の取得（setAttr後の実際の値）
        # リスト表示用なので、共有されている子 (shape/xform本体) と
        # そのparentsも含めて取得する
        nodes_to_read = set(touched_nodes)
        shape_list = instance_data.get(InstanceDetector.TYPE_SHAPE, [])
        xform_list = instance_data.get(InstanceDetector.TYPE_TRANSFORM, [])
        for child, parents in shape_list:
            nodes_to_read.add(child)
            nodes_to_read.update(parents)
        for child, parents in xform_list:
            nodes_to_read.add(child)
            nodes_to_read.update(parents)

        final_color_map = {}
        for node in nodes_to_read:
            c = cls._get_current_color(node)
            if c is not None:
                final_color_map[node] = c

        return count, final_color_map

    @staticmethod
    def _set_color(node, rgb):
        if not cmds.objExists(node):
            return
        try:
            cmds.setAttr("{0}.useOutlinerColor".format(node), 1)
            cmds.setAttr("{0}.outlinerColor".format(node), rgb[0], rgb[1], rgb[2], type="double3")
        except Exception:
            pass

    @staticmethod
    def _get_current_color(node):
        if not cmds.objExists(node):
            return None
        try:
            if not cmds.attributeQuery("useOutlinerColor", node=node, exists=True):
                return None
            if not cmds.getAttr("{0}.useOutlinerColor".format(node)):
                return None
            rgb = cmds.getAttr("{0}.outlinerColor".format(node))[0]
            return (float(rgb[0]), float(rgb[1]), float(rgb[2]))
        except Exception:
            return None

    @classmethod
    def clear_all(cls):
        nodes = cmds.ls(dag=True, long=True) or []
        count = 0
        for n in nodes:
            try:
                if cmds.attributeQuery("useOutlinerColor", node=n, exists=True):
                    if cmds.getAttr("{0}.useOutlinerColor".format(n)):
                        cmds.setAttr("{0}.useOutlinerColor".format(n), 0)
                        cmds.setAttr("{0}.outlinerColor".format(n), 0, 0, 0, type="double3")
                        count += 1
            except Exception:
                pass
        return count

    @classmethod
    def clear_nodes(cls, node_paths):
        """
        指定したノード群 (および各ノードの配下全DAG子孫) のアウトライナカラーを
        リセットする。シーン全体には影響しない。
        """
        if not node_paths:
            return 0
        # 対象ノード + 配下を全部集める
        targets = set()
        for n in node_paths:
            if not cmds.objExists(n):
                continue
            targets.add(n)
            try:
                descendants = cmds.listRelatives(
                    n, allDescendents=True, fullPath=True) or []
                for d in descendants:
                    targets.add(d)
            except Exception:
                pass

        count = 0
        for n in targets:
            try:
                if not cmds.objExists(n):
                    continue
                if cmds.attributeQuery("useOutlinerColor", node=n, exists=True):
                    if cmds.getAttr("{0}.useOutlinerColor".format(n)):
                        cmds.setAttr("{0}.useOutlinerColor".format(n), 0)
                        cmds.setAttr(
                            "{0}.outlinerColor".format(n),
                            0, 0, 0, type="double3")
                        count += 1
            except Exception:
                pass
        return count


# ============================================================
# メインウィンドウ
# ============================================================
class InstanceUtilityWindow(QtWidgets.QDialog):

    WINDOW_NAME = "InstanceUtilityWindow"

    ROLE_NODE_PATH = QtCore.Qt.UserRole + 1
    ROLE_INSTANCE_TYPE = QtCore.Qt.UserRole + 2
    ROLE_IS_PARENT = QtCore.Qt.UserRole + 3

    TYPE_COLOR_SHAPE = QtGui.QColor(100, 160, 220)
    TYPE_COLOR_TRANSFORM = QtGui.QColor(220, 140, 80)
    DEFAULT_NODE_COLOR = QtGui.QColor(210, 210, 210)

    MODE_SELECTED = "selected"
    MODE_ALL = "all"

    # カラム番号
    COL_NODE = 0
    COL_TYPE = 1
    COL_COUNT = 2
    COL_DEPTH = 3

    def __init__(self, parent=None):
        if parent is None:
            parent = get_maya_main_window()
        super(InstanceUtilityWindow, self).__init__(parent)

        self.setObjectName(self.WINDOW_NAME)
        self.setWindowTitle(tr("window_title"))
        self.resize(450, 800)

        self._sync_enabled = True
        self._syncing = False
        self._script_job_id = None
        self._color_map = {}
        self._relink_source = None  # full path of the picked source transform

        self._build_ui()
        self._connect_signals()
        self._register_script_job()
        # 起動時の自動リフレッシュは行わない。
        # シーン内のリファレンスに問題がある場合、起動時のDAG走査で
        # エラーが発生してツール自体が起動できなくなることを避けるため。
        # ユーザーが [リスト更新] ボタンを明示的に押した時のみ列挙を行う。

    def _build_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # === Header row: tool description (left) + language toggle (right) ===
        self.tool_desc = _make_desc_label(tr("tool_description"))
        self.tool_desc.setStyleSheet("""
            QLabel {
                color: #999999;
                font-size: 8pt;
                padding: 2px 2px;
            }
        """)

        self.lang_toggle = LanguageToggle(u"EN", u"VI")
        # Match the initial switch state to the startup language
        self.lang_toggle.setChecked(LANG == "vi")

        header_row = QtWidgets.QHBoxLayout()
        header_row.setSpacing(6)
        header_row.addWidget(self.tool_desc, 1)
        header_row.addWidget(
            self.lang_toggle, 0, QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        main_layout.addLayout(header_row)

        # リストエリア
        self.list_group = QtWidgets.QGroupBox(tr("group_list"))
        list_layout = QtWidgets.QVBoxLayout(self.list_group)
        list_layout.setContentsMargins(6, 12, 6, 6)
        list_layout.setSpacing(4)

        self.btn_refresh = QtWidgets.QPushButton(tr("btn_refresh"))
        self.btn_refresh.setToolTip(tr("tooltip_refresh"))
        self.btn_refresh.setMinimumHeight(22)
        self.btn_refresh.setMaximumHeight(22)
        self.btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #4a6d8c;
                color: #ffffff;
                font-weight: bold;
                font-size: 9pt;
                border: 1px solid #5d8ab0;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #5d8ab0; }
            QPushButton:pressed { background-color: #3a5a75; }
        """)
        list_layout.addWidget(self.btn_refresh)

        # ツリー（4カラムに拡張）
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setColumnCount(4)
        self.tree.setHeaderLabels([
            tr("col_node"), tr("col_type"), tr("col_count"), tr("col_depth")
        ])
        self.tree.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.tree.setAlternatingRowColors(True)
        self.tree.setRootIsDecorated(True)
        header = self.tree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(self.COL_NODE, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(self.COL_TYPE, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(self.COL_COUNT, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(self.COL_DEPTH, QtWidgets.QHeaderView.ResizeToContents)
        list_layout.addWidget(self.tree)

        self.chk_sync = QtWidgets.QCheckBox(tr("label_sync"))
        self.chk_sync.setChecked(True)
        list_layout.addWidget(self.chk_sync)

        main_layout.addWidget(self.list_group, 1)

        # 操作エリア
        subgroup_style = """
            QGroupBox {
                border: 1px solid #555555;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 4px;
                background-color: #3d3d3d;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 6px;
                left: 8px;
                color: #dddddd;
                font-weight: bold;
            }
        """

        self.action_group = QtWidgets.QGroupBox(tr("group_action"))
        action_outer = QtWidgets.QHBoxLayout(self.action_group)
        action_outer.setContentsMargins(6, 12, 6, 6)
        action_outer.setSpacing(8)

        # 変換
        self.convert_group = QtWidgets.QGroupBox(tr("group_convert"))
        self.convert_group.setStyleSheet(subgroup_style)
        convert_layout = QtWidgets.QVBoxLayout(self.convert_group)
        convert_layout.setContentsMargins(8, 14, 8, 8)
        convert_layout.setSpacing(4)

        radio_row = QtWidgets.QHBoxLayout()
        radio_row.setSpacing(6)
        self.radio_selected = QtWidgets.QRadioButton(tr("radio_selected"))
        self.radio_all = QtWidgets.QRadioButton(tr("radio_all"))
        self.radio_selected.setChecked(True)
        self.radio_group = QtWidgets.QButtonGroup(self)
        self.radio_group.addButton(self.radio_selected)
        self.radio_group.addButton(self.radio_all)
        radio_row.addWidget(self.radio_selected)
        radio_row.addWidget(self.radio_all)
        radio_row.addStretch()
        convert_layout.addLayout(radio_row)

        # "Also uninstance descendants" checkbox (only active in Selected mode)
        recursive_row = QtWidgets.QHBoxLayout()
        recursive_row.setSpacing(6)
        self.chk_recursive_uninst = QtWidgets.QCheckBox(
            tr("chk_recursive_uninst"))
        self.chk_recursive_uninst.setChecked(False)
        recursive_row.addWidget(self.chk_recursive_uninst)
        recursive_row.addStretch()
        convert_layout.addLayout(recursive_row)

        # モード切替時にチェックボックスのenable/disableを連動
        def _update_recursive_enabled():
            enabled = self.radio_selected.isChecked()
            self.chk_recursive_uninst.setEnabled(enabled)
        self.radio_selected.toggled.connect(
            lambda _=None: _update_recursive_enabled())
        self.radio_all.toggled.connect(
            lambda _=None: _update_recursive_enabled())
        _update_recursive_enabled()

        self.btn_uninst = QtWidgets.QPushButton(tr("btn_uninstance"))
        self.btn_uninst.setMinimumHeight(46)
        self.btn_uninst.setToolTip(tr("tooltip_uninstance"))
        convert_layout.addStretch()
        convert_layout.addWidget(self.btn_uninst)

        # 複製
        self.dup_group = QtWidgets.QGroupBox(tr("group_duplicate"))
        self.dup_group.setStyleSheet(subgroup_style)
        dup_layout = QtWidgets.QVBoxLayout(self.dup_group)
        dup_layout.setContentsMargins(8, 14, 8, 8)
        dup_layout.setSpacing(4)

        chk_row = QtWidgets.QHBoxLayout()
        chk_row.setSpacing(6)
        self.chk_auto_colorize = QtWidgets.QCheckBox(tr("chk_auto_colorize"))
        self.chk_auto_colorize.setChecked(False)
        chk_row.addWidget(self.chk_auto_colorize)
        chk_row.addStretch()
        dup_layout.addLayout(chk_row)

        self.btn_create_inst = QtWidgets.QPushButton(tr("btn_create_instance"))
        self.btn_create_inst.setMinimumHeight(46)
        self.btn_create_inst.setToolTip(tr("tooltip_duplicate"))
        dup_layout.addStretch()
        dup_layout.addWidget(self.btn_create_inst)

        action_outer.addWidget(self.convert_group, 1)
        action_outer.addWidget(self.dup_group, 1)
        main_layout.addWidget(self.action_group)

        # === Relink area ===
        self.relink_group = QtWidgets.QGroupBox(tr("group_relink"))
        relink_layout = QtWidgets.QVBoxLayout(self.relink_group)
        relink_layout.setContentsMargins(6, 12, 6, 6)
        relink_layout.setSpacing(6)

        # Picked-source name, spanning the full width above the buttons.
        self.relink_source_label = QtWidgets.QLabel(
            tr("relink_source_prefix") + tr("relink_source_none"))
        self.relink_source_label.setStyleSheet(
            "color: #aaaaaa; font-size: 9pt;")
        self.relink_source_label.setWordWrap(False)
        self.relink_source_label.setTextInteractionFlags(
            QtCore.Qt.TextSelectableByMouse)
        relink_layout.addWidget(self.relink_source_label)

        # Two buttons, two columns, on the same row (mirrors Convert/Duplicate).
        relink_btn_row = QtWidgets.QHBoxLayout()
        relink_btn_row.setSpacing(8)

        self.btn_pick_source = QtWidgets.QPushButton(tr("btn_pick_source"))
        self.btn_pick_source.setMinimumHeight(40)
        self.btn_pick_source.setToolTip(tr("tooltip_pick_source"))
        relink_btn_row.addWidget(self.btn_pick_source, 1)

        # Relink button (disabled until a source is picked)
        self.btn_relink = QtWidgets.QPushButton(tr("btn_relink"))
        self.btn_relink.setMinimumHeight(40)
        self.btn_relink.setToolTip(tr("tooltip_relink"))
        self.btn_relink.setEnabled(False)
        relink_btn_row.addWidget(self.btn_relink, 1)

        relink_layout.addLayout(relink_btn_row)

        main_layout.addWidget(self.relink_group)

        # 表示エリア
        self.color_group = QtWidgets.QGroupBox(tr("group_color"))
        color_layout = QtWidgets.QVBoxLayout(self.color_group)
        color_layout.setContentsMargins(6, 12, 6, 6)
        color_layout.setSpacing(6)

        self.btn_apply_color = QtWidgets.QPushButton(tr("btn_apply_color"))
        self.btn_apply_color.setMinimumHeight(40)
        self.btn_apply_color.setToolTip(tr("tooltip_apply_color"))
        color_layout.addWidget(self.btn_apply_color)

        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setStyleSheet("color: #555;")
        color_layout.addWidget(sep)

        self.btn_clear_color = QtWidgets.QPushButton(tr("btn_clear_color"))
        self.btn_clear_color.setMinimumHeight(32)
        self.btn_clear_color.setToolTip(tr("tooltip_clear_color"))
        color_layout.addWidget(self.btn_clear_color)

        main_layout.addWidget(self.color_group)

        # ステータスバー
        status_frame = QtWidgets.QFrame()
        status_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #262626;
                border: 1px solid #555;
                border-radius: 3px;
            }
        """)
        status_layout = QtWidgets.QHBoxLayout(status_frame)
        status_layout.setContentsMargins(8, 5, 8, 5)
        status_layout.setSpacing(8)

        self.status_indicator = QtWidgets.QLabel()
        self.status_indicator.setFixedSize(10, 10)
        self._set_indicator_color("#5a9a5a")

        status_title = QtWidgets.QLabel("STATUS")
        status_title.setStyleSheet(
            "color: #999; font-size: 8pt; font-weight: bold; letter-spacing: 1px;"
        )

        self.status_label = QtWidgets.QLabel(tr("status_ready"))
        self.status_label.setStyleSheet("color: #eeeeee; font-size: 9pt;")

        status_layout.addWidget(self.status_indicator)
        status_layout.addWidget(status_title)
        status_layout.addWidget(self.status_label, 1)

        main_layout.addWidget(status_frame)

    def _set_indicator_color(self, color_str):
        self.status_indicator.setStyleSheet(
            "background-color: {0}; border-radius: 5px; border: 1px solid #222;".format(color_str)
        )

    # シグナル接続
    def _connect_signals(self):
        self.btn_refresh.clicked.connect(self.refresh)
        self.btn_uninst.clicked.connect(self.on_uninstance)
        self.btn_create_inst.clicked.connect(self.on_create_instance)
        self.btn_apply_color.clicked.connect(self.on_apply_color)
        self.btn_clear_color.clicked.connect(self.on_clear_color)
        self.btn_pick_source.clicked.connect(self.on_pick_source)
        self.btn_relink.clicked.connect(self.on_relink)
        self.chk_sync.toggled.connect(self._on_sync_toggled)
        self.tree.itemSelectionChanged.connect(self._on_tree_selection_changed)
        # 言語トグル: toggled(bool) シグナル (True = 英語)
        self.lang_toggle.toggled.connect(self._on_lang_toggled)

    def _on_lang_toggled(self, is_vietnamese):
        """Handle a language toggle (True = Vietnamese, False = English)."""
        global LANG
        LANG = "vi" if is_vietnamese else "en"
        self._retranslate_ui()
        self._set_status(tr("status_ready"), "ok")
        self.refresh()

    def _retranslate_ui(self):
        """Re-apply all UI text based on the current LANG setting."""
        # Window title
        self.setWindowTitle(tr("window_title"))

        # Header description
        self.tool_desc.setText(tr("tool_description"))

        # Group titles
        self.list_group.setTitle(tr("group_list"))
        self.action_group.setTitle(tr("group_action"))
        self.convert_group.setTitle(tr("group_convert"))
        self.dup_group.setTitle(tr("group_duplicate"))
        self.relink_group.setTitle(tr("group_relink"))
        self.color_group.setTitle(tr("group_color"))

        # Buttons
        self.btn_refresh.setText(tr("btn_refresh"))
        self.btn_uninst.setText(tr("btn_uninstance"))
        self.btn_create_inst.setText(tr("btn_create_instance"))
        self.btn_pick_source.setText(tr("btn_pick_source"))
        self.btn_relink.setText(tr("btn_relink"))
        self.btn_apply_color.setText(tr("btn_apply_color"))
        self.btn_clear_color.setText(tr("btn_clear_color"))

        # Tooltips (the old inline descriptions live here now)
        self.btn_refresh.setToolTip(tr("tooltip_refresh"))
        self.btn_uninst.setToolTip(tr("tooltip_uninstance"))
        self.btn_create_inst.setToolTip(tr("tooltip_duplicate"))
        self.btn_pick_source.setToolTip(tr("tooltip_pick_source"))
        self.btn_relink.setToolTip(tr("tooltip_relink"))
        self.btn_apply_color.setToolTip(tr("tooltip_apply_color"))
        self.btn_clear_color.setToolTip(tr("tooltip_clear_color"))

        # Radio buttons / checkboxes
        self.radio_selected.setText(tr("radio_selected"))
        self.radio_all.setText(tr("radio_all"))
        self.chk_recursive_uninst.setText(tr("chk_recursive_uninst"))
        self.chk_auto_colorize.setText(tr("chk_auto_colorize"))
        self.chk_sync.setText(tr("label_sync"))

        # Relink source label (rebuild from the stored source)
        self._update_relink_source_ui()

        # Tree header
        self.tree.setHeaderLabels([
            tr("col_node"), tr("col_type"),
            tr("col_count"), tr("col_depth"),
        ])

    # scriptJob
    def _register_script_job(self):
        try:
            self._script_job_id = cmds.scriptJob(
                event=["SelectionChanged", self._on_scene_selection_changed],
                parent=self.WINDOW_NAME,
                protected=False,
            )
        except Exception:
            try:
                self._script_job_id = cmds.scriptJob(
                    event=["SelectionChanged", self._on_scene_selection_changed],
                    protected=False,
                )
            except Exception as e:
                om.MGlobal.displayWarning(u"scriptJob登録失敗: {0}".format(e))

    def _unregister_script_job(self):
        if self._script_job_id is not None:
            try:
                if cmds.scriptJob(exists=self._script_job_id):
                    cmds.scriptJob(kill=self._script_job_id, force=True)
            except Exception:
                pass
            self._script_job_id = None

    def closeEvent(self, event):
        self._unregister_script_job()
        super(InstanceUtilityWindow, self).closeEvent(event)

    # ツリー構築
    def refresh(self):
        self._syncing = True
        try:
            self.tree.clear()
            data = InstanceDetector.collect()

            shape_list = data[InstanceDetector.TYPE_SHAPE]
            xform_list = data[InstanceDetector.TYPE_TRANSFORM]

            for shape, parents in shape_list:
                depth = InstanceDetector.compute_depth(shape)
                parent_item = self._make_parent_item(
                    shape, InstanceDetector.TYPE_SHAPE, len(parents), depth
                )
                for p in parents:
                    self._make_child_item(parent_item, p, InstanceDetector.TYPE_SHAPE)
                self.tree.addTopLevelItem(parent_item)
                parent_item.setExpanded(False)

            for xform, parents in xform_list:
                depth = InstanceDetector.compute_depth(xform)
                parent_item = self._make_parent_item(
                    xform, InstanceDetector.TYPE_TRANSFORM, len(parents), depth
                )
                for p in parents:
                    self._make_child_item(parent_item, p, InstanceDetector.TYPE_TRANSFORM)
                self.tree.addTopLevelItem(parent_item)
                parent_item.setExpanded(False)

            if not shape_list and not xform_list:
                self._set_status(tr("status_none"), "warn")
            else:
                self._set_status(
                    tr("status_found", shape=len(shape_list), xform=len(xform_list)), "ok"
                )
        finally:
            self._syncing = False

        self._sync_from_scene()

    def _get_node_color(self, node_path):
        """
        色マップから取得。該当がなければデフォルト色を返す。
        アウトライナ側の実際の値と完全一致する。
        """
        rgb = self._color_map.get(node_path)
        if rgb is None:
            return self.DEFAULT_NODE_COLOR
        return QtGui.QColor(int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))

    def _make_parent_item(self, node_path, inst_type, ref_count, depth):
        short_name = node_path.split("|")[-1]
        if inst_type == InstanceDetector.TYPE_SHAPE:
            type_label = tr("shape_instance")
            type_color = self.TYPE_COLOR_SHAPE
        else:
            type_label = tr("transform_instance")
            type_color = self.TYPE_COLOR_TRANSFORM

        item = QtWidgets.QTreeWidgetItem([
            short_name, type_label, str(ref_count), str(depth)
        ])

        node_color = self._get_node_color(node_path)
        item.setForeground(self.COL_NODE, QtGui.QBrush(node_color))
        item.setIcon(self.COL_NODE, self._make_color_icon(node_color))

        item.setForeground(self.COL_TYPE, QtGui.QBrush(type_color))
        font = item.font(self.COL_TYPE)
        font.setBold(True)
        item.setFont(self.COL_TYPE, font)

        item.setForeground(self.COL_COUNT, QtGui.QBrush(self.DEFAULT_NODE_COLOR))
        item.setTextAlignment(self.COL_COUNT, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        item.setForeground(self.COL_DEPTH, QtGui.QBrush(self.DEFAULT_NODE_COLOR))
        item.setTextAlignment(self.COL_DEPTH, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        item.setToolTip(self.COL_NODE, node_path)
        item.setData(self.COL_NODE, self.ROLE_NODE_PATH, node_path)
        item.setData(self.COL_NODE, self.ROLE_INSTANCE_TYPE, inst_type)
        item.setData(self.COL_NODE, self.ROLE_IS_PARENT, True)

        return item

    def _make_child_item(self, parent_item, node_path, inst_type):
        item = QtWidgets.QTreeWidgetItem([u"  └ " + node_path, "", "", ""])
        item.setToolTip(self.COL_NODE, node_path)

        node_color = self._get_node_color(node_path)
        item.setForeground(self.COL_NODE, QtGui.QBrush(node_color))

        item.setData(self.COL_NODE, self.ROLE_NODE_PATH, node_path)
        item.setData(self.COL_NODE, self.ROLE_INSTANCE_TYPE, inst_type)
        item.setData(self.COL_NODE, self.ROLE_IS_PARENT, False)

        parent_item.addChild(item)
        return item

    @staticmethod
    def _make_color_icon(color, size=10):
        pix = QtGui.QPixmap(size, size)
        pix.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pix)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setBrush(QtGui.QBrush(color))
        painter.setPen(QtGui.QPen(QtGui.QColor(40, 40, 40)))
        painter.drawEllipse(1, 1, size-2, size-2)
        painter.end()
        return QtGui.QIcon(pix)

    # 選択同期
    def _on_sync_toggled(self, checked):
        self._sync_enabled = checked
        if checked:
            self._sync_from_scene()

    def _on_tree_selection_changed(self):
        if not self._sync_enabled or self._syncing:
            return
        self._syncing = True
        try:
            nodes = []
            for item in self.tree.selectedItems():
                path = item.data(self.COL_NODE, self.ROLE_NODE_PATH)
                if path and cmds.objExists(path):
                    nodes.append(path)
            if nodes:
                cmds.select(nodes, replace=True)
            else:
                cmds.select(clear=True)
        finally:
            self._syncing = False

    def _on_scene_selection_changed(self):
        if not self._sync_enabled or self._syncing:
            return
        self._sync_from_scene()

    def _sync_from_scene(self):
        if self._syncing:
            return
        self._syncing = True
        try:
            scene_sel = set(cmds.ls(sl=True, long=True) or [])
            self.tree.blockSignals(True)
            try:
                self.tree.clearSelection()
                if not scene_sel:
                    return
                iterator = QtWidgets.QTreeWidgetItemIterator(self.tree)
                first_match = None
                while iterator.value():
                    item = iterator.value()
                    path = item.data(self.COL_NODE, self.ROLE_NODE_PATH)
                    if path and path in scene_sel:
                        item.setSelected(True)
                        if first_match is None:
                            first_match = item
                    iterator += 1
                if first_match is not None:
                    self.tree.scrollToItem(first_match)
            finally:
                self.tree.blockSignals(False)
        finally:
            self._syncing = False

    # アクション
    def _collect_target_nodes(self):
        paths = []
        seen = set()
        for item in self.tree.selectedItems():
            path = item.data(self.COL_NODE, self.ROLE_NODE_PATH)
            if path and path not in seen:
                paths.append(path)
                seen.add(path)
        if paths:
            return paths
        return cmds.ls(sl=True, long=True) or []

    def _get_convert_mode(self):
        return self.MODE_ALL if self.radio_all.isChecked() else self.MODE_SELECTED

    @staticmethod
    def _collect_dag_handles_set():
        """
        現在のシーン内の全DAGノードのMObjectHandle集合を返す。

        MObjectHandle はノード実体を一意に識別するため、リネーム等で
        フルパス文字列が変化しても同じノードは同じハッシュ値を持つ。
        変換処理前後でこの集合の差分を取れば、リネームの影響を受けず
        「真に新規追加されたノード」だけを抽出できる。
        """
        result = set()
        try:
            it = om.MItDag(om.MItDag.kDepthFirst)
            while not it.isDone():
                try:
                    obj = it.currentItem()
                    if not obj.isNull():
                        result.add(om.MObjectHandle(obj))
                except Exception:
                    pass
                it.next()
        except Exception as e:
            om.MGlobal.displayWarning(
                u"DAG列挙失敗: {0}".format(e)
            )
        return result

    @staticmethod
    def _collect_companion_handles(target_paths):
        """
        各処理対象ノードと「インスタンス関係を共有している相手」の
        MObjectHandle集合を返す。処理対象自身のハンドルは除外する。

        Shape選択 (例: Group1/pCube1 のpCubeShape1) の場合は親Transform
        まで遡ってその共有相手を取得する。

        変換後にこのハンドルがインスタンスではなくなっていた場合、
        「処理によって独立ノードになった共有相手」と判定できる。
        """
        result = set()
        target_handles = set()

        # まず処理対象自身のハンドルを記録 (除外用)
        for tgt in target_paths:
            if not cmds.objExists(tgt):
                continue
            try:
                sel = om.MSelectionList()
                sel.add(tgt)
                obj = om.MObject()
                sel.getDependNode(0, obj)
                target_handles.add(om.MObjectHandle(obj))
            except Exception:
                continue

        # 各処理対象の共有相手を列挙
        for tgt in target_paths:
            if not cmds.objExists(tgt):
                continue

            # 1. 処理対象自身のインスタンス共有相手 (Transformインスタンス)
            try:
                tgt_parents = cmds.listRelatives(
                    tgt, allParents=True, fullPath=True) or []
                if len(tgt_parents) >= 2:
                    # 自分のMObjectは1つ。親パスごとに同じMObjectが返る
                    sel = om.MSelectionList()
                    sel.add(tgt)
                    obj = om.MObject()
                    sel.getDependNode(0, obj)
                    h = om.MObjectHandle(obj)
                    if h not in target_handles:
                        result.add(h)
            except Exception:
                pass

            # 2. 配下のShapeインスタンス共有相手
            #    例: tgt = Group1/pCube1, 配下の pCubeShape1 が
            #        Group2/pCube1/pCubeShape1 と共有されているケース
            #    → 共有相手の親 (Group2/pCube1) のMObjectを取得
            try:
                shapes = cmds.listRelatives(
                    tgt, shapes=True, fullPath=True) or []
                for sh in shapes:
                    sh_parents = cmds.listRelatives(
                        sh, allParents=True, fullPath=True) or []
                    if len(sh_parents) < 2:
                        continue
                    # tgt以外の親パスを共有相手とみなす
                    for p in sh_parents:
                        if p == tgt:
                            continue
                        if not cmds.objExists(p):
                            continue
                        try:
                            sel = om.MSelectionList()
                            sel.add(p)
                            obj = om.MObject()
                            sel.getDependNode(0, obj)
                            h = om.MObjectHandle(obj)
                            if h not in target_handles:
                                result.add(h)
                        except Exception:
                            continue
            except Exception:
                pass

        return result

    def on_uninstance(self):
        mode = self._get_convert_mode()
        if mode == self.MODE_ALL:
            ret = QtWidgets.QMessageBox.question(
                self,
                tr("confirm_uninstance_all_title"),
                tr("confirm_uninstance_all_msg"),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No,
            )
            if ret != QtWidgets.QMessageBox.Yes:
                return
            cmds.undoInfo(openChunk=True, chunkName="InstanceUtility_UninstanceAll")
            try:
                count = InstanceOperator.uninstance_all()
                OutlinerColorizer.clear_all()
                self._color_map = {}
            finally:
                cmds.undoInfo(closeChunk=True)
        else:
            nodes = self._collect_target_nodes()
            if not nodes:
                self._set_status(tr("warn_no_instance_selected"), "warn")
                return
            cmds.undoInfo(openChunk=True, chunkName="InstanceUtility_UninstanceSelected")
            try:
                # 変換前に色分けされているかどうかを記録。
                # 色分けされていない (color_map が空) 場合は変換後も
                # 色分けを行わない仕様。
                had_colors = bool(self._color_map)
                # 変換前の色マップをスナップショット (引き継ぎ用)
                inherit_map = dict(self._color_map) if had_colors else {}

                recursive = self.chk_recursive_uninst.isChecked()
                count = InstanceOperator.uninstance_nodes(
                    nodes, recursive=recursive)

                if count > 0:
                    if had_colors:
                        # 変換後の最新インスタンス情報に基づき色を再設定。
                        # 変換前と同じグループには同じ色を引き継ぐ。
                        # 独立化したノードは色グループに属さなくなるため
                        # 自動的に色なし (リセット) となる。
                        OutlinerColorizer.clear_all()
                        data = InstanceDetector.collect()
                        _, color_map = OutlinerColorizer.apply(
                            data, inherit_color_map=inherit_map)
                        self._color_map = color_map
                    else:
                        # 元から色分けされていなければ色分けは行わない。
                        # 既存の色マップは空のまま維持。
                        pass
            finally:
                cmds.undoInfo(closeChunk=True)
        self._set_status(tr("status_uninst_done", n=count), "ok")
        force_outliner_refresh()
        self.refresh()

    def on_create_instance(self):
        sel = cmds.ls(sl=True, long=True) or []
        if not sel:
            self._set_status(tr("warn_no_selection"), "warn")
            return
        cmds.undoInfo(openChunk=True, chunkName="InstanceUtility_CreateInstance")
        try:
            new_nodes, _orig = InstanceOperator.create_instance_from_selection()
            if new_nodes and self.chk_auto_colorize.isChecked():
                data = InstanceDetector.collect()
                _, color_map = OutlinerColorizer.apply(data)
                self._color_map = color_map
        finally:
            cmds.undoInfo(closeChunk=True)
        self._set_status(tr("status_created", n=len(new_nodes)), "ok")
        if self.chk_auto_colorize.isChecked():
            force_outliner_refresh()
        self.refresh()

    def on_apply_color(self):
        data = InstanceDetector.collect()
        cmds.undoInfo(openChunk=True, chunkName="InstanceUtility_ApplyColor")
        try:
            # 事前にアウトライナカラーをリセットしてからapply
            # (既存の色との干渉や残留を防ぐ)
            OutlinerColorizer.clear_all()
            self._color_map = {}
            count, color_map = OutlinerColorizer.apply(data)
            self._color_map = color_map
        finally:
            cmds.undoInfo(closeChunk=True)
        self._set_status(tr("status_color_applied", n=count), "ok")
        force_outliner_refresh()
        self.refresh()

    def on_clear_color(self):
        cmds.undoInfo(openChunk=True, chunkName="InstanceUtility_ClearColor")
        try:
            count = OutlinerColorizer.clear_all()
            self._color_map = {}
        finally:
            cmds.undoInfo(closeChunk=True)
        self._set_status(tr("status_color_cleared", n=count), "ok")
        force_outliner_refresh()
        self.refresh()

    # ---- Relink ----
    def _update_relink_source_ui(self):
        """Refresh the source label text and the Relink button enabled state."""
        src = self._relink_source
        if src and cmds.objExists(src):
            short = src.rsplit("|", 1)[-1]
            self.relink_source_label.setText(
                tr("relink_source_prefix") + short)
            self.relink_source_label.setStyleSheet(
                "color: #7fb37f; font-size: 9pt;")
            self.btn_relink.setEnabled(True)
        else:
            self.relink_source_label.setText(
                tr("relink_source_prefix") + tr("relink_source_none"))
            self.relink_source_label.setStyleSheet(
                "color: #aaaaaa; font-size: 9pt;")
            self.btn_relink.setEnabled(False)

    def on_pick_source(self):
        """Store the first selected transform (with a mesh shape) as source."""
        sel = cmds.ls(sl=True, long=True, transforms=True) or []
        if not sel:
            self._relink_source = None
            self._update_relink_source_ui()
            self._set_status(tr("warn_no_selection"), "warn")
            return

        source = sel[0]
        if InstanceOperator.first_geo_shape(source) is None:
            self._relink_source = None
            self._update_relink_source_ui()
            self._set_status(
                tr("warn_relink_no_mesh", name=source.rsplit("|", 1)[-1]),
                "warn")
            return

        self._relink_source = source
        self._update_relink_source_ui()
        self._set_status(
            tr("status_source_picked", name=source.rsplit("|", 1)[-1]), "ok")

    def on_relink(self):
        source = self._relink_source
        if not source:
            self._set_status(tr("warn_relink_no_source"), "warn")
            return
        if not cmds.objExists(source):
            self._relink_source = None
            self._update_relink_source_ui()
            self._set_status(tr("warn_relink_source_gone"), "err")
            return

        # Targets = current scene selection, minus the source itself.
        sel = cmds.ls(sl=True, long=True, transforms=True) or []
        targets = [t for t in sel if t != source]
        if not targets:
            self._set_status(tr("warn_relink_no_targets"), "warn")
            return

        enforce = True  # topology + pivot are always required for a safe relink
        cmds.undoInfo(openChunk=True, chunkName="InstanceUtility_Relink")
        try:
            relinked, skipped = InstanceOperator.relink_to_source(
                source, targets,
                check_topology=enforce, check_pivot=enforce)
        finally:
            cmds.undoInfo(closeChunk=True)

        for path, reason in skipped:
            om.MGlobal.displayWarning(
                u"Relink skipped [{0}]: {1}".format(reason, path))

        level = "ok" if relinked > 0 else "warn"
        self._set_status(
            tr("status_relink_done", n=relinked, s=len(skipped)), level)
        force_outliner_refresh()
        self.refresh()

    def _set_status(self, msg, level="info"):
        self.status_label.setText(msg)
        colors = {
            "ok":   "#5a9a5a",
            "info": "#4a8ac0",
            "warn": "#c0a040",
            "err":  "#c05050",
        }
        self._set_indicator_color(colors.get(level, colors["info"]))


# ============================================================
# エントリポイント
# ============================================================
_window_instance = None


def show():
    global _window_instance

    if _window_instance is not None:
        try:
            _window_instance.close()
            _window_instance.deleteLater()
        except Exception:
            pass
        _window_instance = None

    for w in QtWidgets.QApplication.allWidgets():
        try:
            name = w.objectName()
        except Exception:
            continue
        if name == InstanceUtilityWindow.WINDOW_NAME:
            try:
                w.close()
                w.deleteLater()
            except Exception:
                pass

    _window_instance = InstanceUtilityWindow()
    _window_instance.show()
    return _window_instance


if __name__ == "__main__":
    show()