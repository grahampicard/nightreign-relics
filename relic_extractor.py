import cv2
import easyocr
import numpy as np


def get_orb_frame(frame):
    height, width, _ = frame.shape
    orb_region = frame[int(height * 0.2) : int(height * 0.6), width // 2 : width]
    return cv2.cvtColor(orb_region, cv2.COLOR_BGR2GRAY)


def _slice_frame(frame, y1, y2, x1, x2, color):
    return cv2.cvtColor(frame[y1:y2, x1:x2], color)


def _coords_to_pair(y1, y2, x1, x2):
    return (x1, y1), (x2, y2)


def get_selected_orb_frame(frame):
    height, width, _ = frame.shape
    orb_region = frame[
        int(height * 0.7) : int(height * 0.8), int(width * 0.50) : int(width * 0.55)
    ]
    return cv2.cvtColor(orb_region, cv2.COLOR_BGR2HSV)


def get_sorting_coords(match):
    bbox = match[0]
    text = match[1]
    x1 = int(bbox[0][0])
    x2 = int(bbox[1][0])
    y1 = int(bbox[0][1])
    y2 = int(bbox[2][1])
    midpoint = ((x2 + x1) / 2, (y2 + y1) / 2)
    return midpoint, text


def split_lines(coords):
    # sort by y first
    midpoints = [get_sorting_coords(x) for x in coords]
    midpoints = sorted(midpoints, key=lambda x: x[0][1])

    # split coordinates into lines
    lines = []
    curline = []

    for i in range(len(midpoints)):
        if i == 0:
            curline.append(midpoints[i])
        else:
            distance = midpoints[i][0][1] - midpoints[i - 1][0][1]
            if distance > 20:
                lines.append(curline)
                curline = [midpoints[i]]
            else:
                curline = sorted(curline, key=lambda x: x[0][0])
                curline.append(midpoints[i])

    curline = sorted(curline, key=lambda x: x[0][0])
    lines.append(curline)

    # sort cur
    return lines


def join_lines_text(lines):
    all_text = []
    for line in lines:
        for _, text in line:
            all_text.append(text)
    return " ".join(all_text)


def extract_relics(
    video_path,
    start_second=0,
    debug=False,
):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open video.")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    start_frame = int(start_second * fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    reader = easyocr.Reader(["en"])
    extracted_data = []

    last_orb_frame = None
    frame_count = start_frame

    while cap.isOpened():
        # image setup. each of these tasks requires scanning a frame for releveant
        # information. bounding boxes (bbox) and such are keyed off of the size
        # of the frame.
        ret, frame = cap.read()
        if not ret:
            break

        height, width, _ = frame.shape
        frame_count += 1

        if debug:
            debug_frame = frame.copy()

        # create bounding boxes which are used for extracting text, and for
        # plotting if debugging.
        orb_bbox = (
            int(height * 0.69),
            int(height * 0.93),
            int(width * 0.47),
            int(width * 0.94),
        )
        label_bbox = (
            int(height * 0.69),
            int(height * 0.75),
            int(width * 0.55),
            int(width * 0.94),
        )
        attr1_bbox = (
            int(height * 0.75),
            int(height * 0.805),
            int(width * 0.55),
            int(width * 0.94),
        )
        attr2_bbox = (
            int(height * 0.805),
            int(height * 0.86),
            int(width * 0.55),
            int(width * 0.94),
        )
        attr3_bbox = (
            int(height * 0.86),
            int(height * 0.93),
            int(width * 0.55),
            int(width * 0.94),
        )
        icon_bbox = (
            int(height * 0.69),
            int(height * 0.83),
            int(width * 0.48),
            int(width * 0.55),
        )

        current_orb_frame = _slice_frame(frame, *orb_bbox, cv2.COLOR_BGR2BGRA)
        current_label_frame = _slice_frame(frame, *label_bbox, cv2.COLOR_BGR2GRAY)
        current_attr1_frame = _slice_frame(frame, *attr1_bbox, cv2.COLOR_BGR2GRAY)
        current_attr2_frame = _slice_frame(frame, *attr2_bbox, cv2.COLOR_BGR2GRAY)
        current_attr3_frame = _slice_frame(frame, *attr3_bbox, cv2.COLOR_BGR2GRAY)
        current_icon_frame = _slice_frame(frame, *icon_bbox, cv2.COLOR_BGR2GRAY)
        diff = np.zeros_like(current_orb_frame)
        non_zero_count = 0

        if last_orb_frame is not None:
            diff = cv2.absdiff(last_orb_frame, current_orb_frame)
            # diff = current_orb_frame - last_orb_frame
            # non_zero_count = np.count_nonzero(diff)
            non_zero_count = np.abs(diff).sum().sum()
            if non_zero_count < 1000000:  # Threshold for change detection
                continue

        # create a new relic data structure
        relic = {"relic": None, "attributes": [], "diff": int(non_zero_count)}

        # first check for the relic label. label is the name of the relic
        # that is to the right of the relic icon
        result = reader.readtext(current_label_frame)
        if result:
            coords = split_lines(result)
            relic["relic"] = join_lines_text(coords)

        # insert relic image check here

        # relics can have up to 3 attributes. extract relic abilities
        # if there is text
        for region in (
            current_attr1_frame,
            current_attr2_frame,
            current_attr3_frame,
        ):
            result = reader.readtext(region)
            if result:
                coords = split_lines(result)
                attr = join_lines_text(coords)
                relic["attributes"].append(attr)

        extracted_data.append(relic)

        # print(
        #     f"frame:\t{frame_count}\tdiff:\t{non_zero_count}\tchange!!\t"
        #     + f"abs:{np.abs(diff).sum().sum()}\trelic:\t{relic['relic']}"
        # )
        #
        if debug:
            cv2.rectangle(debug_frame, *_coords_to_pair(*orb_bbox), (0, 255, 0), 2)
            cv2.rectangle(debug_frame, *_coords_to_pair(*label_bbox), (0, 255, 0), 2)
            cv2.rectangle(debug_frame, *_coords_to_pair(*attr1_bbox), (0, 255, 0), 2)
            cv2.rectangle(debug_frame, *_coords_to_pair(*attr2_bbox), (0, 255, 0), 2)
            cv2.rectangle(debug_frame, *_coords_to_pair(*attr3_bbox), (0, 255, 0), 2)
            cv2.rectangle(debug_frame, *_coords_to_pair(*icon_bbox), (0, 255, 0), 2)
            cv2.imshow("Debug Frame", debug_frame)
            cv2.imshow("orb frame", current_orb_frame)
            if last_orb_frame is not None:
                cv2.imshow("prev orb frame", last_orb_frame)
                cv2.imshow("diff", diff)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            print(non_zero_count)
            breakpoint()

        last_orb_frame = current_orb_frame

    cap.release()
    if debug:
        cv2.destroyAllWindows()

    return extracted_data
