import cv2
import easyocr
import json
import argparse
import numpy as np
import csv


def get_orb_frame(frame):
    height, width, _ = frame.shape
    orb_region = frame[0 : height // 2, width // 2 : width]
    return cv2.cvtColor(orb_region, cv2.COLOR_BGR2GRAY)


def get_text_frame(frame, section="label"):
    height, width, _ = frame.shape

    if section == "label":
        return frame[int(height * 0.69) : int(height * 0.75), width // 2 : width]
    elif section == "attr1":
        return frame[int(height * 0.75) : int(height * 0.81), width // 2 : width]
    elif section == "attr2":
        return frame[int(height * 0.8) : int(height * 0.86), width // 2 : width]
    elif section == "attr3":
        return frame[int(height * 0.87) : int(height * 0.93), width // 2 : width]
    else:
        raise ValueError


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


def export_csv(output_path):
    with open(output_path, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            print(",".join(row))


def main(video_path, output_path, output_format="json", start_second=0, ff_factor=40):
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
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        if frame_count % ff_factor != 0:  # Process every nth frame to speed up
            continue

        current_orb_frame = get_orb_frame(frame)

        if last_orb_frame is not None:
            diff = cv2.absdiff(last_orb_frame, current_orb_frame)
            non_zero_count = np.count_nonzero(diff)

            if non_zero_count > 500:  # Threshold for change detection
                relic = {"relic": None, "attributes": []}

                # extact label
                text_frame = get_text_frame(frame, section="label")
                result = reader.readtext(text_frame)
                if result:
                    coords = split_lines(result)
                    relic["relic"] = join_lines_text(coords)

                for attr in ("attr1", "attr2", "attr3"):
                    text_frame = get_text_frame(frame, section=attr)
                    result = reader.readtext(text_frame)
                    if result:
                        coords = split_lines(result)
                        attr = join_lines_text(coords)
                        relic["attributes"].append(attr)

                extracted_data.append(relic)
                print(
                    f"Change detected at frame {frame_count}, extracted text: {relic}"
                )

        last_orb_frame = current_orb_frame

    cap.release()

    if output_format == "json":
        with open(output_path, "w") as f:
            json.dump(extracted_data, f, indent=4)
    elif output_format == "csv":
        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["index", "relic", "attribute"])
            for i, item in enumerate(extracted_data):
                relic = item["relic"]
                attributes = item["attributes"]
                for attr in attributes:
                    writer.writerow([i, relic, attr])

    print(f"Extraction complete. Data saved to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract text from video based on orb changes."
    )
    parser.add_argument("video_path", help="Path to the input MP4 file.")
    parser.add_argument(
        "--output_path",
        help="Path to the output file. Extension determines format.",
        default=None,
    )
    parser.add_argument(
        "--output_format",
        choices=["json", "csv"],
        default="json",
        help="Format of the output file.",
    )
    parser.add_argument(
        "--start_second",
        type=int,
        default=0,
        help="The second at which to start analyzing the video.",
    )
    parser.add_argument(
        "--ff_factor",
        type=int,
        default=40,
        help="The number of frames to skip per scan.",
    )
    parser.add_argument(
        "--export_csv",
        action="store_true",
        help="Export the CSV file to the console.",
    )
    args = parser.parse_args()

    output_path = args.output_path
    if output_path is None:
        output_path = f"output.{args.output_format}"

    if args.export_csv:
        export_csv(output_path)
    else:
        main(args.video_path, output_path, args.output_format, args.start_second)
