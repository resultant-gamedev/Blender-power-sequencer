import bpy
from bpy.props import EnumProperty, BoolProperty


class GoToMarker(bpy.types.Operator):
    """Moves the time cursor to the next marker"""
    bl_idname = "gdquest_vse.go_to_marker"
    bl_label = "Go to marker"
    bl_options = {'REGISTER', 'UNDO'}

    target_marker = EnumProperty(items=[
        ('left', 'left', 'left'),
        ('right', 'right', 'right')],
        name='Target marker',
        description='Move to the closest marker to the left or to the right of the cursor',
        default='left')

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        if not bpy.context.scene.timeline_markers:
            self.report({"ERROR_INVALID_INPUT"}, "There are no markers. Operation cancelled.")
            return {"CANCELLED"}

        frame = bpy.context.scene.frame_current
        previous_marker, next_marker = find_neighbor_markers(frame)

        if not previous_marker and self.target_marker == 'left' or not next_marker and self.target_marker == 'right':
            self.report({"INFO"}, "No more markers to jump to on the %s side." % self.target_marker)
            return {"CANCELLED"}

        previous_time = previous_marker.frame if previous_marker else None
        next_time = next_marker.frame if next_marker else None

        bpy.context.scene.frame_current = previous_time if self.target_marker == 'left' or not next_time else next_time
        return {'FINISHED'}


class DeleteClosestMarker(bpy.types.Operator):
    bl_idname = 'gdquest_vse.delete_closest_marker'
    bl_label = 'Delete closest marker'
    bl_description = 'Delete the marker closest to the mouse'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        markers = bpy.context.scene.timeline_markers
        if not markers:
            return {"CANCELLED"}

        frame = bpy.context.scene.frame_current

        for m in markers:
            if m.frame == frame:
                markers.remove(m)
                return {'FINISHED'}

        previous_marker, next_marker = find_neighbor_markers(frame)
        marker = None
        if next_marker and previous_marker:
            marker = next_marker if abs(frame-next_marker.frame) <= abs(frame-previous_marker.frame) else previous_marker
        else:
            marker = next_marker if next_marker else previous_marker
        markers.remove(marker)
        return {'FINISHED'}


# TODO: Finish preview
class SetPreviewBetweenMarkers(bpy.types.Operator):
    bl_idname = 'gdquest_vse.set_preview_between_markers'
    bl_label = 'Set preview between closest markers'
    bl_description = "Set the timeline's preview range using the 2 markers closest to the time cursor"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        if not bpy.context.scene.timeline_markers:
            self.report({"ERROR_INVALID_INPUT"}, "There are no markers. Operation cancelled.")
            return {"CANCELLED"}

        frame = None
        if self.reference == 'mouse':
            frame = context.region.view2d.region_to_view(
                x=event.mouse_region_x,
                y=event.mouse_region_y)[0]
        else:
            frame = bpy.context.scene.frame_current

        previous_marker, next_marker = find_neighbor_markers(frame)

        if not (previous_marker and next_marker):
            self.report({"ERROR_INVALID_INPUT"}, "There are no markers. Operation cancelled.")
            return {"CANCELLED"}

        # TODO: If only one marker, set preview from start to marker or from marker to end of last strip

        return {'FINISHED'}


def find_neighbor_markers(frame=None):
    """Returns a tuple containing the closest market to the left and to the right of the frame"""
    markers = bpy.context.scene.timeline_markers

    if not (frame and markers):
        return None, None

    from operator import attrgetter
    markers = sorted(markers, key=attrgetter('frame'))

    previous_marker, next_marker = None, None
    for m in markers:
        previous_marker = m if m.frame < frame else previous_marker
        if m.frame > frame:
            next_marker = m
            break

    return previous_marker, next_marker