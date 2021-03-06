import base64
import multiprocessing as mp
from datetime import datetime
from time import sleep

import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
from rq import get_current_job


def audio_processor(big_file_bytes, little_file_bytes, threshold_line,
                    threads_count, comparision_rate, apply_normalization):
    job = get_current_job()
    job_id = job.id
    try:
        big_file_path = (f'/tmp/{job_id}_big_file.mp3')

        little_file_path = (f'/tmp/{job_id}_little_file.mp3')

        with open(big_file_path, 'wb') as big_file:
            big_file.write(big_file_bytes)

        with open(little_file_path, 'wb') as little_file:
            little_file.write(little_file_bytes)

        # Read audio files and compute spectrogram
        x_1, sr_1 = librosa.load(big_file_path, sr=None)
        spec_1 = librosa.feature.melspectrogram(y=x_1, sr=sr_1)
        _, rows_1 = spec_1.shape

        x_2, sr_2 = librosa.load(little_file_path, sr=None)
        spec_2 = librosa.feature.melspectrogram(y=x_2, sr=sr_2)
        _, rows_2 = spec_2.shape

        # Compute dtw with glide and find the minimum accuracy
        samples_1 = x_1.shape[0]
        # samples_2 = x_2.shape[0]

        costs = mp.Manager().dict()
        advanced = mp.Manager().dict()

        step = int(max(rows_2 * comparision_rate, 1))

        def distances(indices, costs, core, advanced):
            for i, (index, start_row, end_row) in enumerate(indices):
                advanced[core] = (
                    "{}%".format(int((i + 1) / len(indices) * 100))
                )
                D, _ = librosa.dtw(X=spec_1[:, start_row:end_row], Y=spec_2)
                cost = D[-1,-1]
                start_second = (
                    (
                        start_row * samples_1 / rows_1
                    ) / sr_1
                )
                end_second = (
                    end_row * samples_1 / rows_1
                ) / sr_1
                costs[index] = {
                    'cost': cost,
                    'start_row': start_row,
                    'end_row': end_row,
                    'start_second': start_second,
                    'end_second': end_second,
                }

        indices = np.array([
            (i, j, j + rows_2)
            for i, j in enumerate(range(0, rows_1, step))
        ])

        list_indices = np.array_split(indices, threads_count)

        workers = [
            mp.Process(
                target=distances,
                args=(indices, costs, core, advanced)
            )
            for core, indices in enumerate(list_indices)
        ]

        time_start_process = datetime.utcnow()
        for worker in workers:
            worker.start()

        while True in [x.is_alive() for x in workers]:
            job.meta["advanced"] = advanced.values()
            job.save_meta()
            sleep(0.1)
        total_time_process = (
            datetime.utcnow() - time_start_process
        ).total_seconds()

        transformed_costs = {}
        cost_indices = range(max(costs.keys()))
        for cost_index in cost_indices:
            transformed_costs[costs[cost_index].get('cost')] = (
                costs[cost_index].get('start_row'),
                costs[cost_index].get('end_row'),
                costs[cost_index].get('start_second'),
                costs[cost_index].get('end_second'),
            )

        costs_list = transformed_costs.keys()
        min_cost = min(costs_list)

        start_second_list = [
            transformed_costs.get(cost_key)[2] for cost_key in costs_list
        ]

        # First plot
        max_cost = max(costs_list)
        percentage = max_cost * (1 - threshold_line)
        if apply_normalization:
            costs_list = [cl / max_cost for cl in costs_list]
            percentage = 1 - threshold_line

        plt.plot(start_second_list, costs_list)
        plt.axhline(y=percentage, xmin=0.0, xmax=1.0, color='r')
        plt.title('Overlapping distances')
        distances_overlapping_filename = (
            f'/tmp/{job_id}_distances_overlapping.png'
        )
        plt.savefig(distances_overlapping_filename, format='png')

        start_min_cost = transformed_costs.get(min_cost)[0]
        end_min_cost = transformed_costs.get(min_cost)[1]

        start_sample = start_min_cost * samples_1 / rows_1
        end_sample = end_min_cost * samples_1 / rows_1

        start_seconds = start_sample / sr_1
        end_seconds = end_sample / sr_1

        left_matrix = np.zeros(int(start_sample))
        right_matrix = np.zeros(int(samples_1 - end_sample))

        x_2_transformed = np.concatenate(
            (left_matrix, x_2, right_matrix), axis=0
        )

        # Second plot
        plt.figure(figsize=(16, 4))
        librosa.display.waveplot(
            x_1, sr=sr_1, alpha=0.25, max_points=100
        )
        librosa.display.waveplot(
            x_2_transformed, sr=sr_2, color='r', alpha=0.5,
            max_points=100
        )

        plt.title('Best adjust of audio overlapping')
        plt.tight_layout()
        best_adjust_overlapping_filename = (
            f'/tmp/{job_id}_best_adjust_overlapping.png'
        )
        plt.savefig(best_adjust_overlapping_filename, format='png')

        # Prepare results
        b64_png_prefix = b'data:image/png;base64,'

        b64_distances_overlapping_img = b64_png_prefix + base64.b64encode(
            open(distances_overlapping_filename, 'rb').read()
        )

        b64_best_adjust_overlapping_img = b64_png_prefix + base64.b64encode(
            open(best_adjust_overlapping_filename, 'rb').read()
        )

        results = {
            'advanced': advanced.values(),
            'results': {
                'big_file_sampling_frequency': sr_1,
                'little_file_sampling_frequency': sr_2,
                'distances_overlapping_img': b64_distances_overlapping_img,
                'best_adjust_overlapping_img': b64_best_adjust_overlapping_img,
                'start_second': start_seconds,
                'end_second': end_seconds,
                'process_duration': total_time_process,
                'step_info': {'step': step, 'end': rows_1},
                'finished': True
            }
        }

        job.meta = {**job.meta, **results}
        job.save_meta()
    except Exception as e:
        job.meta = {**job.meta, 'error': str(e)}
        job.save_meta()
