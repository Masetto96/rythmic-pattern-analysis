from pathlib import Path
import pandas as pd
import numpy as np
import librosa
from scripts.scale_transform_magnitude import compute_stm, compute_stm_multi_channel



def load_brid_dataset(multi_channel_stm = False, stm_params: dict = {}):
    data_path = Path("../datasets/BRID/Data/Solo Tracks")
    if multi_channel_stm:
        stm_func = compute_stm_multi_channel
    else:
        stm_func = compute_stm
    instrument, labels, features = [], [], []
    for parent_folder in data_path.iterdir():
        for i in range(1, 4):
            if str(i) in parent_folder.name:
                print(f"Processing folder: {parent_folder.name}")
                metadata = pd.read_excel("../datasets/BRID/BRID - Description.xlsx", sheet_name=f"Solos - Instrumentalist {i}")
                for subfolder in parent_folder.iterdir():
                    print(subfolder.name)
                    metadata_instrument = metadata[metadata["Instrument"].str.contains(subfolder.name, case=False, na=False)]
                    for row in metadata_instrument.itertuples(index=False):
                        file_name = f"[{row[1]}] {row[2]}.wav"
                        try:
                            y, sr = librosa.load(subfolder / file_name, sr=None, duration=30)
                            stm, *_ = stm_func(y=y, sr=sr, **stm_params)    
                            features.append(stm)
                        except FileNotFoundError:
                            # print(e)
                            file_name = f"[0{row[1]}] {row[2]}.wav"
                            y, sr = librosa.load(subfolder / file_name, sr=None, duration=30)
                            stm, *_ = stm_func(y=y, sr=sr, **stm_params)    
                            features.append(stm)
                        finally:
                            labels.append(row[4])
                            instrument.append(row[3])

    hover_data_brid = pd.DataFrame({"pattern": labels, "instrument": instrument, "tradition": "Brazilian"})

    return features, labels, hover_data_brid


def process_malian_jembe_annotation(row, audio_file_path):
    """
    Processing the row of the annotation file.

    Returns
    -------
    y: np.ndarray
        Audio signal.
    sr: int
        Sample rate.
    label: str
        Label, in this case consisting of pattern type.
    """
    y, sr = librosa.load(audio_file_path, offset=row.start, duration=row.duration)
    label = row.label
    return y, sr, label


def load_malian_jembe_dataset(multi_channel_stm = False, stm_params: dict = {}):
    """
    Audio segments are loaded based on time-stamps contained in the annotations.

    Returns
    -------
    features_mj: list
        List of feature vectors.
    labels_mj: list
        List of labels.
    hover_data_mj: pandas.DataFrame
        DataFrame with hover data.
    """
    mj_media = Path("../datasets/MJ/Media")
    mj_annotations = Path("../datasets/MJ/Annotations")

    features_mj, labels_mj = [], []

    pattern, tradition, instrument = [], [], []

    columns = ["category", "start", "end", "duration", "label"]

    durations = []

    if multi_channel_stm:
        stm_func = compute_stm_multi_channel
    else:
        stm_func = compute_stm

    # Iterate over annotation folders
    for parent_folder in mj_annotations.iterdir():
        if parent_folder.is_dir():
            # Define the path to the audio files
            audio_files_path = mj_media / parent_folder.name

            # Iterate over annotation files
            for annot in parent_folder.glob("*Annotation.csv"):
                print(f"Processing annotation file: {annot.name}")

                # Read the annotation CSV file
                annot_df = pd.read_csv(
                    annot,
                    header=None,
                    names=columns,
                    dtype={"start": float, "end": float, "duration": float},
                )

                # Filter the rows for category "MUSIC_FORM" and duration > 10
                annot_df = annot_df[
                    (annot_df["category"] == "MUSIC_FORM") & (annot_df["duration"] > 10)
                ]

                # Extract the ensemble number from the annotation file name
                ensemble_num = annot.name.rstrip("Annotation.csv")

                # Iterate over audio files
                for audio_file in audio_files_path.glob("*.wav"):
                    if ensemble_num in audio_file.name:
                        print(f"Processing audio file: {audio_file}")

                        # Iterate over rows in the annotation data frame
                        for row in annot_df.itertuples(index=False):
                            # Append the duration to the durations list
                            durations.append(row.duration)

                            # Process the ensemble and extract the feature
                            y, sr, label = process_malian_jembe_annotation(
                                row=row, audio_file_path=audio_file
                            )

                            # Creating label: pattern type + audio file name
                            label = f"{label}_{audio_file.stem}"
                            # Append the label and feature to the corresponding lists
                            labels_mj.append(label)
                            stm, *_ = stm_func(y=y, sr=sr, **stm_params)
                            features_mj.append(stm)

                            # Split the label and append parts to the corresponding lists
                            parts = label.split("_")
                            if len(parts) >= 3:
                                pattern.append(parts[0])
                                tradition.append(parts[2])
                                instrument.append(parts[4])

    # Create the hover data DataFrame
    hover_data_mj = pd.DataFrame(
        {"pattern": pattern, "instrument": instrument, "tradition": tradition}
    )
    hover_data_mj["label"] = tradition
    hover_data_mj = hover_data_mj.reset_index(drop=True)

    # Print the duration median
    print(f"Features shape: {len(features_mj)} -- labels shape: {len(labels_mj)}")
    print(f"Duration median: {np.median(durations)} seconds")

    return features_mj, labels_mj, hover_data_mj


def load_candombe_dataset(multi_channel_stm = False, stm_params: dict = {}):
    """
    Each wav file is segmented into 20 second long non-overlapping segments.

    Returns:
        features_candombe (list): A list of feature vectors.
        labels_candombe (list): A list of corresponding labels.
        hover_data_candombe (DataFrame): A DataFrame with additional information for hovering in the visualization.
    """
    if multi_channel_stm:
        stm_func = compute_stm_multi_channel
    else:
        stm_func = compute_stm

    # Path to the Candombe dataset
    candombe_media = Path("../datasets/candombe/Media")

    # Lists to store the features, labels, and instrument information
    labels_candombe, features_candombe = [], []

    # Iterate over all wav files in the dataset
    for file in candombe_media.rglob("*.wav"):
        label = file.stem.split("_")[-1]

        # Skip the stereo mix files
        if label == "Stereo":
            continue

        print(f"Processing file: {file.name}")

        # Load the audio file
        y, sr = librosa.load(file)

        # Segment length in seconds
        segment_length = 30

        # Iterate over the segments
        for start in range(0, len(y), segment_length * sr):
            # Compute the STM for the segment
            segment = y[start : start + segment_length * sr]
            if (len(segment) / sr) != segment_length: # discarding the last segment basically
                continue 
            stm, *_ = stm_func(y=segment, sr=sr, **stm_params)

            # Append the feature and label
            features_candombe.append(stm)
            labels_candombe.append(f"{label}_{start // (segment_length * sr)}")

    # Split the label and append parts to the corresponding lists
    pattern, instrument = [], []
    for label in labels_candombe:
        parts = label.split("_")
        pattern.append(parts[1])
        instrument.append(parts[0])

    # Create the hover data DataFrame
    hover_data_candombe = pd.DataFrame({"pattern": pattern, "instrument": instrument})
    hover_data_candombe["tradition"] = "Candombe"
    hover_data_candombe["label"] = instrument
    hover_data_candombe = hover_data_candombe.reset_index(drop=True)

    print(
        f"Features shape: {len(features_candombe)} -- labels shape: {len(labels_candombe)}"
    )

    return features_candombe, labels_candombe, hover_data_candombe


def load_cretan_dances_dataset(multi_channel_stm = False, stm_params: dict = {}):
    cretan_dances_data_path = Path("../datasets/CretanDances")
    features, labels, audio_files_paths = [], [], []
    if multi_channel_stm:
        stm_func = compute_stm_multi_channel
    else:
        stm_func = compute_stm

    for subfolder in cretan_dances_data_path.iterdir():
        if subfolder.is_dir():
            label = subfolder.name
            print(f"Processing folder: {label}")
            for audio_file in subfolder.glob("*.wav"):
                y, sr = librosa.load(audio_file, sr=None, duration=30)
                stm, *_ = stm_func(y, sr, **stm_params)
                features.append(stm)
                labels.append(label)
                audio_files_paths.append(audio_file.stem)

    hover_data_cretan = pd.DataFrame({"pattern": audio_files_paths, "instrument": None})
    hover_data_cretan["tradition"] = "CretanDances"
    hover_data_cretan["label"] = labels

    return features, labels, hover_data_cretan


def load_ballroom_dataset(multi_channel_stm = False, stm_params: dict = {}):
    dataset_path = Path("../datasets/BallroomData")
    features, labels, audio_files_paths = [], [], []
    if multi_channel_stm:
        stm_func = compute_stm_multi_channel
    else:
        stm_func = compute_stm

    for parent_folder in dataset_path.iterdir():
        if parent_folder.is_dir():
            if parent_folder.name == "nada":
                continue
            print(f"Processing folder: {parent_folder.name}")
            label = parent_folder.name.lower()
            for audio_file in parent_folder.glob("*.wav"):
                y, sr = librosa.load(audio_file, sr=None, duration=30)
                # stm = compute_stm(y, sr, **stm_params)
                stm, *_ = stm_func(y, sr, **stm_params)
                features.append(stm)
                labels.append(label)
                audio_files_paths.append(audio_file.stem)

    hover_data_ballroom = pd.DataFrame(
        {
            "pattern": audio_files_paths,
            "instrument": None,
            "tradition": "Ballroom",
            "label": labels,
        }
    )
    hover_data_ballroom = hover_data_ballroom.reset_index(drop=True)

    print(f"Features shape: {len(features)} -- labels shape: {len(labels)}")

    return features, labels, hover_data_ballroom
