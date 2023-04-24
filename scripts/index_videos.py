import os
import pinecone
import cv2
import typing
import scenedetect as sd
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel
import csv

API_KEY = os.environ['PINEAPI']
INDEX_NAME = "clipmoviescenes250"

clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")


def collect_scenes_in_video(
    video_path: str,
) -> typing.List[typing.Tuple[sd.FrameTimecode, sd.FrameTimecode]]:
    video = sd.open_video(video_path)
    sm = sd.SceneManager()
    sm.add_detector(sd.ContentDetector(threshold=27.0))
    sm.detect_scenes(video)

    return sm.get_scene_list()


def clip_embeddings(image: Image):
    inputs = clip_processor(images=image, return_tensors="pt", padding=True)
    with torch.no_grad():
        image_embeddings = clip_model.get_image_features(**inputs)
    return image_embeddings


def scene_features(video_path: str, no_of_samples: int = 3):
    scenes = collect_scenes_in_video(video_path)

    cap = cv2.VideoCapture(video_path)
    scenes_frame_samples = []

    for scene_idx in range(len(scenes)):
        scene_length = abs(
            scenes[scene_idx][0].frame_num - scenes[scene_idx][1].frame_num
        )
        every_n = round(scene_length / no_of_samples)
        local_samples = [
            (every_n * n) + scenes[scene_idx][0].frame_num for n in range(no_of_samples)
        ]
        scenes_frame_samples.append(local_samples)

    if len(scenes) == 0:
        # this could denote a single contiguous scene.
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if frame_count > 0:
            every_n = round(frame_count / no_of_samples)
            local_samples = [(every_n * n) for n in range(no_of_samples)]
            scenes_frame_samples.append(local_samples)

    scene_clip_embeddings = []
    for scene_idx in range(len(scenes_frame_samples)):        
        try:
            scene_start = scenes[scene_idx][0].get_seconds()
            scene_end = scenes[scene_idx][1].get_seconds()

            scene_samples = scenes_frame_samples[scene_idx]
            pixel_tensors = []

            for frame_sample in scene_samples:
                cap.set(1, frame_sample)
                ret, frame = cap.read()
                if not ret:
                    print("breaks oops", ret, frame_sample, scene_idx, frame)
                    break
                pil_image = Image.fromarray(frame)
                clip_pixel_values = clip_embeddings(pil_image)
                pixel_tensors.append(clip_pixel_values)

            avg_pix = torch.mean(torch.stack(pixel_tensors), dim=0)
            
            scene_clip_embeddings.append(
                (avg_pix, scene_start, scene_end)
            )
        except: 
            print('failed iter for some reason')

    return scene_clip_embeddings


def index_video(
    index: pinecone.Index,
    path: str,
    id: str,
    movie_name: str,
    release_year: str,
    scene_title: str,
    poster: str,
):
    file_path = os.path.join(path, id) + ".mp4"

    if os.path.isfile(file_path):
        features = scene_features(file_path, no_of_samples=3)

        for idx, f in enumerate(features):
            embed, start, end = f

            image_embeddings = embed.cpu().numpy().tolist()            

            try:
                index.upsert(
                    vectors=[
                        (
                            f"{id}_{idx}",
                            image_embeddings,
                            {
                                "scene_no": idx,
                                "start": start,
                                "end": end,
                                "index_id": id,
                                "poster": poster,
                                "scene_title": scene_title,
                                "release_year": release_year,
                                "movie_name": str(
                                    str(movie_name).encode("ascii", "ignore")
                                ),
                            },
                        ),
                    ],
                )
            except Exception as e:
                print("FAILED TO UPSERT", e)


from tqdm import tqdm

def insert_videos(video_dir: str, csv_path: str):
    index = pinecone.Index(index_name=INDEX_NAME)

    with open(csv_path) as csvfile:
        reader = csv.DictReader(csvfile)
        total_rows = sum(1 for _ in reader)
        csvfile.seek(0)

        reader = csv.DictReader(csvfile)

        for row in tqdm(reader, total=total_rows):            
            index_video(
                index,
                video_dir,
                row["ID"],
                row["Movie Title"],
                row["Year"],
                row["Scene Title"],
                row['Cover URL'],
            )


def main(video_dir: str, csv_path: str):
    pinecone.init(api_key=API_KEY, environment="us-east4-gcp")

    insert_videos(video_dir, csv_path)


if __name__ == "__main__":
    import sys

    video_dir = sys.argv[1]
    csv_path = sys.argv[2]

    main(video_dir, csv_path)
