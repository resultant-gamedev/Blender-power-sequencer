"""Sequence selection and editing related functions"""
import bpy
from .global_settings import SequenceTypes, SearchMode


def find_empty_channel(mode='ABOVE'):
    """Finds and returns the first empty channel in the VSE
    Takes the optional argument mode: 'ABOVE' or 'ANY'
    'ABOVE' finds the first empty channel above all of the other strips
    'ANY' finds the first empty channel, even if there are strips above it"""
    sequences = bpy.context.sequences

    if not sequences:
        return 1

    empty_channel = None
    channels = [s.channel for s in sequences]
    channels = sorted(list(set(channels)))

    for i in range(channels[-1]):
        if i not in channels:
            if mode == 'ANY':
                empty_channel = i
                break
    if not empty_channel:
        empty_channel = channels[-1] + 1

    return empty_channel


def is_channel_free(target_channel, start_frame, end_frame):
    """Checks if the selected channel is empty or not. Optionally verifies that
       there is space in the channel in a certain timeframe"""
    sequences = [s for s in bpy.context.sequences if s.channel == target_channel]

    for s in sequences:
        if start_frame <= s.frame_final_start <= end_frame or start_frame <= s.frame_final_end <= end_frame:
            return False
    return True


# TODO: refactor code - clean up / get the user to pass sequences to work on?
def find_next_sequences(mode=SearchMode.NEXT,
                        sequences=None,
                        pick_sound=False):
    """Returns a sequence or a list of sequences following the active one"""
    if not sequences:
        sequences = bpy.context.scene.sequence_editor.sequences
        if not sequences:
            return None

    active = bpy.context.scene.sequence_editor.active_strip
    nexts = []
    nexts_far = []
    same_channel = []

    # Find all selected sequences to the right of the active sequence
    for seq in sequences:

        if (seq.frame_final_start >= active.frame_final_end) or (
                seq.frame_final_start > active.frame_final_start) & (
                    seq.frame_final_start < active.frame_final_end) & (
                        seq.frame_final_end > active.frame_final_end):
            if abs(seq.channel - active.channel) > 2:
                nexts_far.append(seq)
            elif seq.type in SequenceTypes.SOUND and not pick_sound:
                pass
            else:
                nexts.append(seq)
                if mode is SearchMode.CHANNEL and \
                   seq.channel == active.channel:
                    same_channel.append(seq)

    # Store the sequences to return
    next_sequences = None
    if mode is SearchMode.CHANNEL:
        return same_channel
    elif len(nexts) > 0:
        return min(
            nexts,
            key=lambda next: (next.frame_final_start - active.frame_final_start))
    elif len(nexts_far) > 0:
        next_sequences = min(nexts_far, key=lambda next: (
            next.frame_final_start - active.frame_final_start))

    return next_sequences


def select_strip_handle(sequences, side=None, frame=None):
    """Select the left or right handles of the strips based on the frame number"""
    if not side and sequences and frame:
        return False

    side = side.upper()

    for seq in sequences:
        seq.select_left_handle = False
        seq.select_right_handle = False

        handle_side = ''

        start, end = seq.frame_final_start, seq.frame_final_end

        if side == 'AUTO' and start <= frame <= end:
            handle_side = 'LEFT' if abs(
                frame - start) < seq.frame_final_duration / 2 else 'RIGHT'
        elif side == 'LEFT' and frame < end or side == 'RIGHT' and frame > start:
            handle_side = side
        else:
            seq.select = False
        if handle_side:
            bpy.ops.sequencer.select_handles(side=handle_side)
    return True


def mouse_select_sequences(frame=None, channel=None, mode='mouse', select_linked=True):
    """Selects sequences based on the mouse position or using the time cursor"""

    selection = []
    sequences = bpy.context.sequences

    if not sequences:
        return []

    for seq in sequences:
        channel_check = True if seq.channel == channel else False
        if channel_check and seq.frame_final_start <= frame <= seq.frame_final_end:
            selection.append(seq)
            if mode == 'mouse' or mode == 'smart' and channel_check:
                break

    if len(selection) > 0:
        # Select linked time sequences
        if select_linked and mode in ('mouse', 'smart'):
            for seq in sequences:
                if seq.channel != selection[0].channel \
                   and seq.frame_final_start == selection[0].frame_final_start \
                   and seq.frame_final_end == selection[0].frame_final_end:
                    selection.append(seq)
    # In smart mode, if we don't get any selection, we select everything
    elif mode == 'smart':
        selection = sequences
    return selection


# FIXME: getting all blocks but 1
def slice_selection(sequences):
    """Takes a list of sequences and returns a list of lists of connected sequences"""
    if not sequences:
        return None

    # order the sequences by starting frame.
    from operator import attrgetter
    sequences = sorted(sequences, key=attrgetter('frame_final_start'))

    last_sequence = sequences[0]
    break_indices = []
    index = 1
    for s in sequences:
        if not s.frame_final_start <= last_sequence.frame_final_end:
            break_indices.append(index)
        last_sequence = s
        index += 1

    # print(break_indices)

    # Create lists
    last_breakpoint = break_indices[0]
    broken_selection = []
    index = 0
    for next_breakpoint in break_indices:
        temp_list = []
        for counter in range(last_breakpoint, next_breakpoint):
            temp_list.append(sequences[counter])
        if temp_list:
            broken_selection.append(temp_list)
        index += 1
    # print(len(broken_selection))
    return broken_selection


def get_frame_range(sequences):
    """Returns a tuple containing the starting frame and the
    end frame of the passed sequences, as displayed in the VSE"""
    if not sequences:
        return False

    from operator import attrgetter
    sequences = sorted(sequences, key=attrgetter('frame_final_start'))
    start = min(sequences, key=attrgetter('frame_final_start')).frame_final_start
    end = max(sequences, key=attrgetter('frame_final_end')).frame_final_end
    return start, end


def set_preview_range(start, end):
    """Sets the preview range and timeline render range"""
    if not start and end:
        raise ValueError('Missing start or end parameter')

    scene = bpy.context.scene
    scene.frame_start = start
    scene.frame_end = end
    scene.frame_preview_start = start
    scene.frame_preview_end = end
    return True


def reset_preview_range():
    """Sets the preview and timeline render start and end frames to
    1 and the end of the last strip"""
    sequences = bpy.context.scene.sequence_editor.sequences
    if not sequences:
        return None
    frame_start = 1

    from operator import attrgetter
    frame_end = max(bpy.context.scene.sequence_editor.sequences,
                    key=attrgetter('frame_final_end')).frame_final_end
    set_preview_range(frame_start, frame_end)
    return True