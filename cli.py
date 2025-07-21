import argparse
import json
import csv
from api.relic_extractor import extract_relics


def main():
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
        "--export_csv",
        action="store_true",
        help="Export the CSV file to the console.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode to display frames with bounding boxes.",
    )
    args = parser.parse_args()

    output_path = args.output_path
    if output_path is None:
        output_path = f"output.{args.output_format}"

    extracted_data = extract_relics(
        args.video_path,
        args.start_second,
        debug=args.debug,
    )

    if args.output_format == "json":
        with open(output_path, "w") as f:
            json.dump(extracted_data, f, indent=4)
    elif args.output_format == "csv":
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
    main()
