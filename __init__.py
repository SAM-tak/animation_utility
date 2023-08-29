#
# Keyframe Edit utilities
#

bl_info = {
    "name": "Animation Utility",
    "author": "SAMtak",
    "version": (0, 1),
    "blender": (3, 2, 0),
    "location": "Dopesheet Editor Menu, Graph Editor Menu",
    "description": "Animation Utility Tools",
    "support": "COMMUNITY",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Animation"
}

"""
Keyframe Edit utilities
"""

import bpy
import sys
import math
from mathutils import Quaternion


class RemoveLockedChannelOperator(bpy.types.Operator):
    bl_idname = "animutils.remove_locked_channels"
    bl_label = "Remove Locked Channels"
    bl_description = "Remove Locked Channels"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.area.type == 'DOPESHEET_EDITOR':
            for i in context.area.spaces:
                if i.type == 'DOPESHEET_EDITOR' and (i.mode == 'DOPESHEET' or i.mode == 'ACTION') and i.action:
                    return True
        return False

    def execute(self, context):
        #print("exec %s" % (self.bl_idname))
        dopesheet = None
        action = None
        for i in context.area.spaces: #find the dopesheet
            if i.type == 'DOPESHEET_EDITOR' and (i.mode == 'DOPESHEET' or i.mode == 'ACTION') and i.action:
                dopesheet = i
                action = dopesheet.action
                break

        #print(dopesheet.type)
        if action:
            removee_fcurve = []
            localdic = {'context' : context}
            for i in action.groups:
                for j in i.channels:
                    if j.data_path.endswith('.location'):
                        if eval("context.active_object.%s.lock_location[%d]" % (j.data_path[0:-9], j.array_index), None, localdic):
                            removee_fcurve.append(j)
                    elif j.data_path.endswith('.scale'):
                        if eval("context.active_object.%s.lock_scale[%d]" % (j.data_path[0:-6], j.array_index), None, localdic):
                            removee_fcurve.append(j)
                    elif j.data_path.endswith('.rotation_quaternion'):
                        if eval("context.active_object.%s.rotation_mode" % j.data_path[0:-20], None, localdic) == 'QUATERNION':
                            if j.array_index < 3:
                                if eval("context.active_object.%s.lock_rotation[%d]" % (j.data_path[0:-20], j.array_index), None, localdic):
                                    removee_fcurve.append(j)
                            else:
                                if eval("context.active_object.%s.lock_rotation_w" % j.data_path[0:-20], None, localdic):
                                    removee_fcurve.append(j)
                        else:
                            removee_fcurve.append(j)
                    elif j.data_path.endswith('.rotation_euler'):
                        if eval("context.active_object.%s.rotation_mode" % j.data_path[0:-15], None, localdic) != 'QUATERNION':
                            if eval("context.active_object.%s.lock_rotation[%d]" % (j.data_path[0:-15], j.array_index), None, localdic):
                                removee_fcurve.append(j)
                        else:
                            removee_fcurve.append(j)

            for fcurve in removee_fcurve:
                action.fcurves.remove(fcurve)

        return {'FINISHED'}


class RemoveInvalidChannelOperator(bpy.types.Operator):
    bl_idname = "animutils.remove_invalid_channels"
    bl_label = "Remove Invalid Channels"
    bl_description = "Remove Invalid Channels"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.area.type == 'DOPESHEET_EDITOR':
            for i in context.area.spaces:
                if i.type == 'DOPESHEET_EDITOR' and (i.mode == 'DOPESHEET' or i.mode == 'ACTION') and i.action:
                    return True
        return False

    def execute(self, context):
        #print("exec %s" % (self.bl_idname))
        dopesheet = None
        action = None
        for i in context.area.spaces: #find the dopesheet
            if i.type == 'DOPESHEET_EDITOR' and (i.mode == 'DOPESHEET' or i.mode == 'ACTION') and i.action:
                dopesheet = i
                action = dopesheet.action
                break

        #print(dopesheet.type)
        if action:
            removee_fcurve = []
            localdic = {'context' : context}
            for i in action.groups:
                for j in i.channels:
                    if j.data_path.endswith('.location'):
                        pass
                    elif j.data_path.endswith('.scale'):
                        pass
                    elif j.data_path.endswith('.rotation_quaternion'):
                        pass
                    elif j.data_path.endswith('.rotation_euler'):
                        pass
                    else:
                        try:
                            eval(f"context.active_object.{j.data_path}", None, localdic)
                        except Exception:
                            removee_fcurve.append(j)

            for fcurve in removee_fcurve:
                action.fcurves.remove(fcurve)

        return {'FINISHED'}

    @staticmethod
    def menu_fn(menu, context):
        menu.layout.separator()
        menu.layout.operator(RemoveLockedChannelOperator.bl_idname)
        menu.layout.operator(RemoveInvalidChannelOperator.bl_idname)

    @classmethod
    def register(cls):
        bpy.types.DOPESHEET_MT_channel.append(cls.menu_fn)

    @classmethod
    def unregister(cls):
        bpy.types.DOPESHEET_MT_channel.remove(cls.menu_fn)


class MakeShortestPathQuatsOperator(bpy.types.Operator):
    bl_idname = "animutils.make_shortest_path_quats"
    bl_label = "Make Shortest Path Quats"
    bl_description = "Make Shortest Path Quats"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(context.selected_editable_fcurves) > 0

    def execute(self, context):
        targets = {}
        for fcurve in context.selected_editable_fcurves:
            if fcurve.data_path.endswith('.rotation_quaternion'):
                for p in fcurve.keyframe_points:
                    if p.select_control_point:
                        if fcurve.data_path not in targets:
                            targets[fcurve.data_path] = [
                                [None, None, None, None], # fcurve
                                [[], [], [], []]          # keyframe
                            ]
                        targets[fcurve.data_path][0][fcurve.array_index] = fcurve
                        targets[fcurve.data_path][1][fcurve.array_index].append(p)

        for k in targets:
            quats = {}
            v = targets[k]
            print(k, len(v))
            #print(v[0][0], v[0][1], v[0][2], v[0][3])
            #print(len(v[1][0]), len(v[1][1]), len(v[1][2]), len(v[1][3]))
            for i in range(4):
                for kf in v[1][i]:
                    if kf.co[0] not in quats:
                        q = Quaternion((math.nan, math.nan, math.nan, math.nan))
                        quats[kf.co[0]] = q
                    quats[kf.co[0]][i] = kf.co[1]
            for kf in quats:
                q = quats[kf]
                for i in range(4):
                    if v[0][i] and math.isnan(q[i]):
                        q[i] = v[0][i].evaluate(kf)
            pkf = math.nan
            need_updates = {}
            for kf in sorted(quats.keys()):
                if not math.isnan(pkf):
                    pq = quats[pkf]
                    cq = quats[kf]
                    #print(pkf, kf, pq.dot(cq) < pq.dot(-cq), pq.dot(cq), pq.dot(-cq))
                    if pq.dot(cq) < pq.dot(-cq):
                        need_updates[kf] = quats[kf] = -cq
                        #sys.stdout.write(' %f' % kf)
                pkf = kf
            if len(need_updates) > 0:
                #print('update!')
                for i in range(4):
                    for kf in v[1][i]:
                        if kf.co[0] in need_updates:
                            q = need_updates[kf.co[0]]
                            kf.co[1] = q[i]
                    v[0][i].update()

        return {'FINISHED'}


class RemoveSequencedKeyframeOperator(bpy.types.Operator):
    bl_idname = "animutils.remove_sequenced_keyframe"
    bl_label = "Remove Sequenced Keyframe"
    bl_description = "Remove Sequenced Keyframe"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(context.selected_editable_fcurves) > 0

    def execute(self, context):
        for fc in context.selected_editable_fcurves:  # It is valid because has been already polled
            pkf = None
            in_seq = False
            removee_kf = []
            if len(fc.keyframe_points) > 1:
                for i in sorted([kf.co[0] for kf in fc.keyframe_points][0:-2]):
                    if pkf is not None:
                        if i - pkf > 2.0:
                            if in_seq:
                                removee_kf.append(i)
                            in_seq = False
                        else:
                            removee_kf.append(i)
                            in_seq = True
                    pkf = i

                print(removee_kf)
                for kf in removee_kf:
                    for i in range(0, len(fc.keyframe_points)):
                        if fc.keyframe_points[i].co[0] == kf:
                            fc.keyframe_points.remove(fc.keyframe_points[i])
                            break

                fc.update()

        return {'FINISHED'}


class ClampEulerAngleOperator(bpy.types.Operator):
    bl_idname = "animutils.clamp_euler_angle"
    bl_label = "Clamp Euler Angle"
    bl_description = "Clamp Euler Angle"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(context.selected_editable_fcurves) > 0

    @staticmethod
    def removeframe(keyframe_points, kf):
        for i in range(0, len(keyframe_points)):
            if keyframe_points[i].co[0] == kf:
                keyframe_points.remove(keyframe_points[i])
                break

    def execute(self, context):
        #print("exec %s" % (self.bl_idname))
        action = context.active_object.animation_data.action
        #print(dopesheet.type)
        for fc in context.selected_editable_fcurves:  # It is valid because has been already polled
            if fc.data_path.endswith('rotation_euler') and fc.select:
                print(fc.data_path)
                for kfp in fc.keyframe_points:
                    value = kfp.co[1]
                    #print(value)
                    if value > math.pi or value < -math.pi:
                        while value > math.pi:
                            value -= math.pi * 2
                        while value < -math.pi:
                            value += math.pi * 2
                        #print(value)
                        kfp.co[1] = value
                fc.update()

        return {'FINISHED'}

    @staticmethod
    def menu_fn(menu, context):
        menu.layout.separator()
        menu.layout.operator(MakeShortestPathQuatsOperator.bl_idname)
        menu.layout.operator(RemoveSequencedKeyframeOperator.bl_idname)
        menu.layout.operator(ClampEulerAngleOperator.bl_idname)
    
    @classmethod
    def register(cls):
        bpy.types.GRAPH_MT_key.append(cls.menu_fn)

    @classmethod
    def unregister(cls):
        bpy.types.GRAPH_MT_key.remove(cls.menu_fn)


namemap = {
    "あ" : "mth.A",
    "い" : "mth.I",
    "う" : "mth.U",
    "え" : "mth.E",
    "お" : "mth.O",
    "あ２" : "mth.A2",
    "ワ" : "mth.smile",
    "にやり" : "mth.grin",
    "まばたき" : "eye.close",
    "ウィンク２" : "eye.close_strong.L",
    "ｳｨﾝｸ右2" : "eye.close_strong.R",
    "笑い" : "eye.smile",
    "ウィンク" : "eye.close.L",
    "ウィンク右" : "eye.close.R",
    "じと目" : "eye.doubt",
    "瞳小" : "eye.small",
    "真面目" : "blw.SERIOUS",
    "にこり" : "blw.smile",
    "怒り" : "blw.ang",
    "困る" : "blw.sap",
    "上" : "blw.up",
    "下" : "blw.down",
    "い２" : "mth.I2",
    "い３" : "mth.I3",
    "▽" : "mth.D",
    "~" : "mth.shy",
    "へ" : "mth.dis",
    "□" : "mth.shock",
    "∨" : "mth.V",
    "にか" : "mth.smile2",
    "にか2" : "mth.smile3"
}

def tobonename(shapekeyname):
    if shapekeyname in namemap:
        mapped = namemap[shapekeyname]
        if mapped != "":
            return 'sk.' + mapped
    else:
        return shapekeyname if shapekeyname.startswith('sk.') else 'sk.' + shapekeyname
    return None


class SetUpShapeKeyDriver(bpy.types.Operator):
    bl_idname = "animutils.setup_shape_key_driver"
    bl_label = "Set Up Shape Key Driver"
    bl_description = "Set up shape key drivers drive by bone position"
    bl_options = {'REGISTER', 'UNDO'}

    @staticmethod
    def setup(mesh, armature, context):
        #print(mesh, armature)
        # Select armature
        mesh.select = False
        armature.select = True
        armature.hide = False
        context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='EDIT')

        for i in mesh.data.shape_keys.key_blocks:
            if mesh.data.shape_keys.reference_key != i:
                #print(i)
                bone_name = tobonename(i.name)
                if bone_name is None or bone_name in armature.data.edit_bones:
                    #print('available')
                    pass
                else:
                    print('new bone', bone_name)
                    edit_bone = armature.data.edit_bones.new(bone_name)
                    bone_name = edit_bone.name
                    edit_bone.use_deform = False
                    edit_bone.head = (0, 0, 0)
                    edit_bone.tail = (0, 0, 0.3)
                    edit_bone.roll = 0

        bpy.ops.object.mode_set(mode='POSE')
        for i in mesh.data.shape_keys.key_blocks:
            if mesh.data.shape_keys.reference_key != i:
                print(i)
                bone_name = tobonename(i.name)
                print(bone_name)
                if bone_name is not None and bone_name in armature.pose.bones:
                    #print('available')
                    pbone = armature.pose.bones[bone_name]
                    pbone.lock_location = (True, True, True)
                    pbone.lock_rotation = (False, True, True)
                    pbone.lock_rotation_w = True
                    pbone.lock_scale = (True, True, True)

        mesh.select = True
        armature.select = False
        context.view_layer.objects.active = mesh
        for i in mesh.data.shape_keys.key_blocks:
            if mesh.data.shape_keys.reference_key != i:
                bone_name = i.name

                bone_name = tobonename(i.name)

                if bone_name is not None and bone_name in armature.pose.bones:
                    if not mesh.data.shape_keys.animation_data:
                        mesh.data.shape_keys.animation_data_create()

                    fcurve = None
                    for j in mesh.data.shape_keys.animation_data.drivers:
                        if j.driver.type == 'SCRIPTED' and j.data_path == 'key_blocks["%s"].value' % i.name:
                            fcurve = j

                    if fcurve is None:
                        #print('new driver', i.name)
                        fcurve = mesh.data.shape_keys.key_blocks[i.name].driver_add('value')
                        fcurve.driver.variables.new()
                    else:
                        #print('available')
                        pass

                    if fcurve:
                        fcurve.driver.expression = 'min(1, max(0, var / (pi / 2)))'
                        fcurve.driver.variables[0].name = 'var'
                        fcurve.driver.variables[0].type = 'TRANSFORMS'
                        fcurve.driver.variables[0].targets[0].id = armature
                        fcurve.driver.variables[0].targets[0].bone_target = bone_name
                        fcurve.driver.variables[0].targets[0].transform_type = 'ROT_X'
                        fcurve.driver.variables[0].targets[0].transform_space = 'LOCAL_SPACE'
                        fcurve.update()

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and len(context.active_object.modifiers) > 0\
            and any((i for i in context.active_object.modifiers if i.type == 'ARMATURE'))

    def execute(self, context):
        print("exec %s" % (self.bl_idname))
        if context.active_object:
            if len(context.active_object.modifiers) > 0:
                for i in context.active_object.modifiers:
                    if i.type == 'ARMATURE':
                        self.setup(context.active_object, i.object, context)

        return {'FINISHED'}
    
    @staticmethod
    def menu_fn(menu, context):
        menu.layout.separator()
        menu.layout.operator(SetUpShapeKeyDriver.bl_idname, icon='DRIVER')

    @classmethod
    def register(cls):
        bpy.types.MESH_MT_shape_key_context_menu.append(cls.menu_fn)

    @classmethod
    def unregister(cls):
        bpy.types.MESH_MT_shape_key_context_menu.remove(cls.menu_fn)


class ConvertToBoneAnimationFromShapeKeyAnimation(bpy.types.Operator):
    bl_idname = "animutils.convert_to_bone_animation"
    bl_label = "Convert To Bone Animation"
    bl_description = "Convert To Bone Animation From Shape Key Animation"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def convert(cls, dstaction, srcaction):
        for i in srcaction.groups:
            bone_name = tobonename(i.name)
            if bone_name and len(i.channels) > 0:
                dstgroup = None
                if bone_name in dstaction.groups:
                    dstgroup = dstaction.groups[bone_name]
                else:
                    dstgroup = dstaction.groups.new(bone_name)
                data_path = 'pose.bones["%s"].location' % bone_name
                dstfcurve = None
                for j in dstaction.fcurves:
                    if j.data_path == data_path and j.array_index == 2:
                        dstfcurve = j
                        break
                if dstfcurve:
                    dstaction.fcurves.remove(dstfcurve)
                dstfcurve = dstaction.fcurves.new(data_path, 2, dstgroup.name)
                srcfcurve = i.channels[0]
                for j in srcfcurve.keyframe_points:
                    dstfcurve.keyframe_points.insert(j.co[0], j.co[1])
                dstfcurve.update()

    @classmethod
    def poll(cls, context):
        if context.area.type == 'DOPESHEET_EDITOR':
            for i in context.area.spaces:
                if i.type == 'DOPESHEET_EDITOR' and i.mode == 'SHAPEKEY' and i.action:
                    return True
        return False

    def execute(self, context):
        print("exec %s" % (self.bl_idname))
        dopesheet = None
        srcaction = None
        for i in context.area.spaces: #find the dopesheet
            if i.type == 'DOPESHEET_EDITOR' and i.mode == 'SHAPEKEY' and i.action:
                dopesheet = i
                srcaction = dopesheet.action
                break

        if context.active_object:
            if len(context.active_object.modifiers) > 0:
                dstaction = None
                for i in context.active_object.modifiers:
                    if i.type == 'ARMATURE':
                        dstaction = i.object.animation_data.action
                if dstaction is None:
                    dstaction = bpy.data.actions.new(srcaction.name)
                self.convert(dstaction, srcaction)

        return {'FINISHED'}

    @staticmethod
    def menu_fn(menu, context):
        menu.layout.separator()
        menu.layout.operator(ConvertToBoneAnimationFromShapeKeyAnimation.bl_idname)

    @classmethod
    def register(cls):
        bpy.types.DOPESHEET_MT_key.append(cls.menu_fn)

    @classmethod
    def unregister(cls):
        bpy.types.DOPESHEET_MT_key.remove(cls.menu_fn)


register, unregister = bpy.utils.register_classes_factory((
    MakeShortestPathQuatsOperator,
    RemoveLockedChannelOperator,
    RemoveInvalidChannelOperator,
    RemoveSequencedKeyframeOperator,
    ClampEulerAngleOperator,
    SetUpShapeKeyDriver,
    ConvertToBoneAnimationFromShapeKeyAnimation
))

if __name__ == "__main__":
    register()
