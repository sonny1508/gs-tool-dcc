# -*- coding: utf-8 -*-

###################################################
"""

kmjDuplicateCopyWeight
・選択したメッシュを複製し、ウェイトコピーを行うスクリプトです。
・スキニングされたメッシュを編集した際、skinCluster以外のヒストリを消したい時に使用します
・複数メッシュ選択に対応していますが、階層選択はされません
・skinClusterを持たないメッシュは無視されます
・ラティスなどのデフォーマーを使うとコピーの際に誤差が出ることがあります

■更新履歴
・2022/07/08　アトリビュートのアンロックができていなかったのを修正
・2020/05/27　フリーズの設定が効いていなかったのを修正
            複数メッシュを跨ぐデフォーマーがある場合ウェイトが消えてしまったのを修正
・2020/04/16 「Copy to Non-Weight Meshes」追加
            各種フリーズ機能追加。それに伴ってUI無し版の仕様変更
・2020/03/25 元のインフルエンスから変更しないよう修正
・2019/11/14 GUI実装。複製、ノンデフォーマーヒストリのみ削除の機能追加。不要なShapeOrigを削除するように修正

■既知の問題
Maya2022は未対応です
同位置且つウェイト値の違う頂点はウェイトコピーが上手くできません


■スクリプトをkmjDuplicateCopyWeight.pyというファイル名でスクリプトフォルダに保存して、スクリプトエディターに下記を入力して実行します。
###ここから
import kmjDuplicateCopyWeight
kmjDuplicateCopyWeight.main()
###ここまで

■GUIを使用しない場合（GUIを出さずにシェルフ等に登録したい場合）は下記で実行可能です。
###ここから
import kmjDuplicateCopyWeight
kmj_object = kmjDuplicateCopyWeight.KMJ_DuplicateCopyWeight()
kmj_object.duplicateCopyWeight(1,1,1,1,1)
###ここまで

上記kmj_object.duplicateCopyWeight(n1,n2,n3,n4,n5)のカッコ内の数値で設定を変更できます。
n1:
 1:ウェイト付きの複製
 2:ウェイトを保持したまま不要なヒストリを削除
 3:ノンデフォーマーヒストリのみ削除（undoすると壊れるため非推奨）
 4:スキンクラスターを持たないメッシュにウェイトコピー
n2~n5:
 n2:移動値のフリーズ　1:ON, 0:OFF
 n3:回転値のフリーズ　1:ON, 0:OFF
 n4:スケール値のフリーズ　1:ON, 0:OFF
 n5:ピボット位置のフリーズ　1:ON, 0:OFF

"""
###################################################
from functools import partial
import maya.cmds as cmds


class KMJ_DuplicateCopyWeight(object):
    def __init__(self):
        self.window = 'kmjDuplicateCopyWeight'
        self.title = 'kmjDuplicateCopyWeight'
        self.size = (300, 300)

    def create(self):
        if cmds.window('kmjDuplicateCopyWeight', exists=True):
            cmds.deleteUI('kmjDuplicateCopyWeight', window=True)
        self.window = cmds.window(
            self.window,
            t=self.title,
            widthHeight=self.size
        )
        self.layout()
        cmds.showWindow()

    def layout(self):
        self.formLayout01 = cmds.formLayout(numberOfDivisions=100)
        self.textLabel = cmds.text(l='Freeze:', align='left')
        self.checkbox_translate = cmds.checkBox(l='Translate', v=True)
        self.checkbox_rotate = cmds.checkBox(l='Rotate', v=True)
        self.checkbox_scale = cmds.checkBox(l='Scale', v=True)
        self.checkbox_pivot = cmds.checkBox(l='Pivot', v=True)
        self.button01 = cmds.button(l='Duplicate with Weight', c=self.duplicateWithWeightButton,
                                    ann='Duplicate the mesh while retaining the skin weight.')
        self.button02 = cmds.button(l='Delete History and Keep Weight', c=self.deleteHistoryKeepWeightButton,
                                    ann='Removes history while retaining the skin weight.')
        self.button03 = cmds.button(l='Delete Non-Deformer and Keep Weight', c=self.deleteNonDeformerKeepWeightButton,
                                    ann='Remove the non-deformer history while retaining the skin weight.')
        self.button04 = cmds.button(l='Copy to Non-Weight Meshes', c=self.copyNonWeightMeshButton,
                                    ann='1.Select the source mesh. 2.Select the target mesh. 3.Click this button.')
        cmds.formLayout(self.formLayout01, edit=True, \
                        attachPosition=(
                            (self.textLabel, 'top', 5, 0), \
                            (self.textLabel, 'left', 20, 0), \
                            (self.textLabel, 'bottom', 1, 5), \
                            (self.textLabel, 'right', 20, 100), \
 \
                            (self.checkbox_translate, 'top', 0, 8), \
                            (self.checkbox_translate, 'left', 20, 0), \
                            (self.checkbox_translate, 'bottom', 0, 19), \
                            (self.checkbox_translate, 'right', 5, 40), \
 \
                            (self.checkbox_rotate, 'top', 0, 8), \
                            (self.checkbox_rotate, 'left', 5, 30), \
                            (self.checkbox_rotate, 'bottom', 0, 19), \
                            (self.checkbox_rotate, 'right', 20, 60), \
 \
                            (self.checkbox_scale, 'top', 0, 8), \
                            (self.checkbox_scale, 'left', 5, 60), \
                            (self.checkbox_scale, 'bottom', 0, 19), \
                            (self.checkbox_scale, 'right', 5, 80), \
 \
                            (self.checkbox_pivot, 'top', 0, 19), \
                            (self.checkbox_pivot, 'left', 20, 0), \
                            (self.checkbox_pivot, 'bottom', 0, 30), \
                            (self.checkbox_pivot, 'right', 5, 40), \
 \
                            (self.button01, 'top', 5, 30), \
                            (self.button01, 'left', 20, 0), \
                            (self.button01, 'bottom', 5, 47), \
                            (self.button01, 'right', 20, 100), \
 \
                            (self.button02, 'top', 5, 47), \
                            (self.button02, 'left', 20, 0), \
                            (self.button02, 'bottom', 5, 64), \
                            (self.button02, 'right', 20, 100), \
 \
                            (self.button03, 'top', 5, 64), \
                            (self.button03, 'left', 20, 0), \
                            (self.button03, 'bottom', 5, 81), \
                            (self.button03, 'right', 20, 100), \
 \
                            (self.button04, 'top', 5, 81), \
                            (self.button04, 'left', 20, 0), \
                            (self.button04, 'bottom', 5, 98), \
                            (self.button04, 'right', 20, 100)
                        )
                        )

    def undoRecord(func):
        def wrapper(*args, **kwargs):
            cmds.undoInfo(openChunk=True)
            try:
                return func(*args, **kwargs)
            except Exception as e:
                raise
            finally:
                cmds.undoInfo(closeChunk=True)

        return wrapper

    # 実行部。GUI無し版のコマンドを兼ねる
    @undoRecord
    def duplicateCopyWeight(self, option, trans_check, rotate_check, scale_check, pivot_check, *args):
        sel = cmds.ls(sl=True)
        if option == 1:  # ウェイト付き複製
            self.duplicateWithWeight(sel, trans_check, rotate_check, scale_check, pivot_check)
        elif option == 2:  # ウェイトを残してヒストリ整理
            self.deleteHisotryKeepWeight(sel, trans_check, rotate_check, scale_check, pivot_check)
        elif option == 3:  # ノンデフォーマーヒストリの削除
            self.deleteNonDeformerKeepWeight(sel, trans_check, rotate_check, scale_check, pivot_check)
        elif option == 4:  # バインド＆ウェイトコピー
            self.bindCopyWeight(sel, trans_check, rotate_check, scale_check, pivot_check)

    # button01コマンド
    def duplicateWithWeightButton(self, *args):
        trans_check, rotate_check, scale_check, pivot_check = self.get_option()
        self.duplicateCopyWeight(1, trans_check, rotate_check, scale_check, pivot_check)

    # button02コマンド
    def deleteHistoryKeepWeightButton(self, *args):
        trans_check, rotate_check, scale_check, pivot_check = self.get_option()
        self.duplicateCopyWeight(2, trans_check, rotate_check, scale_check, pivot_check)

    # button03コマンド
    def deleteNonDeformerKeepWeightButton(self, *args):
        trans_check, rotate_check, scale_check, pivot_check = self.get_option()
        self.duplicateCopyWeight(3, trans_check, rotate_check, scale_check, pivot_check)

    # button04コマンド
    def copyNonWeightMeshButton(self, *args):
        trans_check, rotate_check, scale_check, pivot_check = self.get_option()
        self.duplicateCopyWeight(4, trans_check, rotate_check, scale_check, pivot_check)

    # ウェイト付き複製
    def duplicateWithWeight(self, sel, trans_check, rotate_check, scale_check, pivot_check, *args):
        new_objs = []
        for obj in sel:
            sc = self.get_history(obj)
            if sc is not None:
                joint_list = cmds.skinCluster(sc, q=True, inf=True)
                max_influences = cmds.skinCluster(sc, q=True, mi=True)
                maintain_max_influences = cmds.getAttr(sc + '.maintainMaxInfluences')

                new_obj = cmds.duplicate(obj)[0]
                self.freezeTransform(new_obj, trans_check, rotate_check, scale_check, pivot_check)    # 各種フリーズ

                # 新しいメッシュにskinClusterを作成しウェイトコピー
                new_sc = cmds.skinCluster(joint_list, new_obj, mi=max_influences, omi=maintain_max_influences, tsb=True)[0]
                cmds.copySkinWeights(ss=sc, ds=new_sc, nm=True, sa='closestPoint', ia=('oneToOne', 'name'))
                self.delete_unused_shape(new_obj)  # 不要なShapeOrig削除
                new_objs.append(new_obj)
                print((obj + " : done"))
            else:
                print((obj + " : skinCluster is not found"))
        cmds.select(cl=True)
        cmds.select(new_objs, add=True)

    # ウェイトを残してヒストリ整理
    def deleteHisotryKeepWeight(self, sel, trans_check, rotate_check, scale_check, pivot_check, *args):
        new_objs = []
        for obj in sel:
            sc = self.get_history(obj)
            if sc is not None:
                joint_list = cmds.skinCluster(sc, q=True, inf=True)
                max_influences = cmds.skinCluster(sc, q=True, mi=True)
                maintain_max_influences = cmds.getAttr(sc + '.maintainMaxInfluences')

                new_obj = cmds.duplicate(obj)[0]
                self.freezeTransform(new_obj, trans_check, rotate_check, scale_check, pivot_check)    # 各種フリーズ

                # 新しいメッシュにskinClusterを作成しウェイトコピー
                new_sc = cmds.skinCluster(joint_list, new_obj, mi=max_influences, omi=maintain_max_influences, tsb=True)[0]
                cmds.copySkinWeights(ss=sc, ds=new_sc, nm=True, sa='closestPoint', ia=('oneToOne', 'name'))
                self.delete_unused_shape(new_obj)  # 不要なShapeOrig削除
                temp_name = self.get_name(obj)
                old_obj = cmds.rename(obj, temp_name + "_old")
                #print (cmds.ls(old_obj, l=True))
                new_obj = cmds.rename(new_obj, temp_name)
                #print (cmds.ls(new_obj, l=True))
                new_objs.append(new_obj)
                cmds.delete(old_obj)
                print((new_obj + " : done"))
            else:
                print((obj + " : skinCluster is not found"))
        cmds.select(cl=True)
        print(new_objs)
        cmds.select(new_objs, add=True)

    # ノンデフォーマーヒストリの削除
    def deleteNonDeformerKeepWeight(self, sel, trans_check, rotate_check, scale_check, pivot_check, *args):
        target_objs = []
        source_objs = []
        source_scs = []
        infl_sets = []
        mi_sets = []
        omi_sets = []
        
        for obj in sel:
            sc = self.get_history(obj)
            if sc is not None:
                joint_list = cmds.skinCluster(sc, q=True, inf=True)
                max_influences = cmds.skinCluster(sc, q=True, mi=True)
                maintain_max_influences = cmds.getAttr(sc + '.maintainMaxInfluences')
                temp_obj = cmds.duplicate(obj)[0]
                self.freezeTransform(temp_obj, trans_check, rotate_check, scale_check, pivot_check)  # 各種フリーズ
                # 新しいメッシュにskinClusterを作成しウェイト退避
                temp_sc = cmds.skinCluster(joint_list, temp_obj, mi=max_influences, omi=maintain_max_influences, tsb=True)[0]
                cmds.copySkinWeights(ss=sc, ds=temp_sc, nm=True, sa='closestPoint', ia=('oneToOne', 'name'))
                self.delete_unused_shape(temp_obj)  # 不要なShapeOrig削除
                # コピペ用リストに追加
                target_objs.append(obj)
                source_objs.append(temp_obj)
                source_scs.append(temp_sc)
                infl_sets.append(joint_list)
                mi_sets.append(max_influences)
                omi_sets.append(maintain_max_influences)
            else:
                print((obj + " : skinCluster is not found"))
        # 元のメッシュのフリーズ
        for i in range(len(target_objs)):
            self.freezeTransform(target_objs[i], trans_check, rotate_check, scale_check, pivot_check)
        # 元のメッシュのヒストリ削除
        cmds.select(cl=True)
        cmds.select(target_objs, add=True)
        cmds.bakePartialHistory(ppt=True)
        # スキンクラスタを作成してウェイトを戻す
        for i in range(len(target_objs)):
            new_sc = self.get_history(target_objs[i])    # スキンクラスタは既にあるので取得のみ
            cmds.select(cl=True)
            cmds.select(source_objs[i], add=True)
            cmds.select(target_objs[i], add=True)
            cmds.copySkinWeights(ss=source_scs[i], ds=new_sc, nm=True, sa='closestPoint', ia=('oneToOne', 'name'))
            cmds.delete(source_objs[i])
            self.delete_unused_shape(target_objs[i])  # 不要なShapeOrig削除
            print((target_objs[i] + " : done"))
        cmds.select(cl=True)
        cmds.select(target_objs, add=True)


    # 自動バインドとウェイトコピー
    def bindCopyWeight(self, sel, trans_check, rotate_check, scale_check, pivot_check, *args):
        sc = self.get_history(sel[0])
        if sc is not None:
            sel.pop(0)    # 最初のobjを取り出してリストから削除
            # 各種設定を取得
            joint_list = cmds.skinCluster(sc, q=True, inf=True)
            max_influences = cmds.skinCluster(sc, q=True, mi=True)
            maintain_max_influences = cmds.getAttr(sc + '.maintainMaxInfluences')

            # ターゲットメッシュにskinClusterを作成しウェイト退避
            for target_obj in sel:
                self.freezeTransform(target_obj, trans_check, rotate_check, scale_check, pivot_check)  # 各種フリーズ
                new_sc = self.get_history(target_obj)
                if new_sc is None:
                    new_sc = cmds.skinCluster(joint_list, target_obj, mi=max_influences, omi=maintain_max_influences, tsb=True)[0]
                    cmds.copySkinWeights(ss=sc, ds=new_sc, nm=True, sa='closestPoint', ia=('oneToOne', 'name'))
                    self.delete_unused_shape(target_obj)  # 不要なShapeOrig削除
                else:    # ターゲットにskinClusterが既にある場合はそのままウェイトコピー
                    cmds.copySkinWeights(ss=sc, ds=new_sc, nm=True, sa='closestPoint', ia=('oneToOne', 'name'))
                    self.delete_unused_shape(target_obj)  # 不要なShapeOrig削除
            return sel
        else:
            print((sel[0] + " : skinCluster is not found"))

    # 各種フリーズ
    def freezeTransform(self, obj, trans_check, rotate_check, scale_check, pivot_check, *args):
        cmds.setAttr(obj + '.translate', lock=False)
        cmds.setAttr(obj + '.tx', lock=False)
        cmds.setAttr(obj + '.ty', lock=False)
        cmds.setAttr(obj + '.tz', lock=False)
        cmds.setAttr(obj + '.rotate', lock=False)
        cmds.setAttr(obj + '.rx', lock=False)
        cmds.setAttr(obj + '.ry', lock=False)
        cmds.setAttr(obj + '.rz', lock=False)
        cmds.setAttr(obj + '.scale', lock=False)
        cmds.setAttr(obj + '.sx', lock=False)
        cmds.setAttr(obj + '.sy', lock=False)
        cmds.setAttr(obj + '.sz', lock=False)
        if trans_check:
            cmds.makeIdentity(obj, a=True, t=True)
        if rotate_check:
            cmds.makeIdentity(obj, a=True, r=True)
        if scale_check:
            cmds.makeIdentity(obj, a=True, s=True)
        if pivot_check:
            cmds.setAttr(obj + '.rotatePivot', 0, 0, 0)
            cmds.setAttr(obj + '.scalePivot', 0, 0, 0)
        cmds.setAttr(obj + '.tx', lock=True)
        cmds.setAttr(obj + '.ty', lock=True)
        cmds.setAttr(obj + '.tz', lock=True)
        cmds.setAttr(obj + '.rx', lock=True)
        cmds.setAttr(obj + '.ry', lock=True)
        cmds.setAttr(obj + '.rz', lock=True)
        cmds.setAttr(obj + '.sx', lock=True)
        cmds.setAttr(obj + '.sy', lock=True)
        cmds.setAttr(obj + '.sz', lock=True)

    # 設定の読み込み
    def get_option(self, *args):
        trans_bool = cmds.checkBox(self.checkbox_translate, q=True, v=True)
        rotate_bool = cmds.checkBox(self.checkbox_rotate, q=True, v=True)
        scale_bool = cmds.checkBox(self.checkbox_scale, q=True, v=True)
        pivot_bool = cmds.checkBox(self.checkbox_pivot, q=True, v=True)
        return trans_bool, rotate_bool, scale_bool, pivot_bool

    # ヒストリからskinClusterを検索して返す
    def get_history(self, obj, *args):
        for history in cmds.listHistory(obj):
            obj_type = cmds.objectType(history)
            if obj_type == 'skinCluster':
                return history

    # オブジェクト名が重複してフルパスで取得されていた時用
    def get_name(self, obj, *args):
        split_name = obj.rsplit('|', 1)
        return split_name[-1]

    # 不要なShapeOrigを削除
    def delete_unused_shape(self, obj, *args):
        mesh_list = cmds.listRelatives(obj, s=True, pa=True, f=True, typ='mesh')
        for mesh_node in mesh_list:
            history = cmds.listHistory(mesh_node, f=True)
            if len(history) <= 1:
                cmds.delete(mesh_node)


def main():
    kmjDuplicateCopyWeight = KMJ_DuplicateCopyWeight()
    kmjDuplicateCopyWeight.create()