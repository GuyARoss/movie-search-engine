import json
from youtubesearchpython import ChannelSearch, ResultMode

import csv


def query_movie_clips_from_yt(movie: str):
    search = ChannelSearch(f"{movie} movieclips", "UC3gNmTGu-TTbFPpfSs5kNkg")
    return json.loads(search.result(mode=ResultMode.json))["result"][:5]


def download_youtube_video(url: str, path: str, filename: str) -> str:
    try:
        from pytube import YouTube

        yt = YouTube(url)
        return (
            yt.streams.filter(progressive=True, file_extension="mp4")
            .order_by("resolution")
            .desc()
            .first()
            .download(path, filename=f"{filename}.mp4")
        )

    except Exception as e:
        print("error: youtube downloader: ", e.__str__())
    except:
        print(f"failed download? {url}")


def main(videos_csv):
    final = []

    with open(videos_csv, "r", newline="") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)

        for row in reader:
            movie_title = row[0]
            year = row[1]

            try:
                clips = query_movie_clips_from_yt(f"{movie_title} ({year})")
            except:
                print(f"skipping clip collection for {movie_title} ({year})")
                continue

            for clip in clips:
                if clip["type"] == "playlist":
                    continue

                duration = clip["duration"]["simpleText"]

                parsed_duration = str(duration).split(":")
                if len(parsed_duration) > 2:
                    continue

                if int(parsed_duration[0]) > 4 and int(parsed_duration[1]) > 30:
                    continue

                id = clip["id"]
                title = clip["title"]

                download_path = download_youtube_video(
                    f"https://www.youtube.com/watch?v={id}", "videos", id
                )
                if download_path != None:
                    final.append([id, movie_title, year, title])
                    print(download_path)

    with open("movie_scene_affiliation.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["ID", "Movie Title", "Year", "Scene Title"])
        writer.writerows(final)


if __name__ == "__main__":
    import sys

    video_csv = sys.argv[1]
    main(video_csv)
