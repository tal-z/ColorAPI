from io import BytesIO
# import requests
import aiohttp
import asyncio
import aiofiles

# Basic Algo Plan
# 
# 1.  Start with a collection of color values.
# 2.  Select K positions (pixels) within the collection (pixel array), 
#     and find which seed position each other position in the collection 
#     is closest to (based on it's color using hsv distance). Label each 
#     position with that seed position.
# 3.  Take each sub-collection of lables, and calculate each of their 
#     averages (centroid).
# 4.  Take our set of k centroids, and for each member in our collection
#     find which centroid it is closest to. Label it as such.
# 5.  Take each sub-collection of labels, and calculate each of their 
#     averages (centroid).
# 6.  Compare new centroids to old centroids. If new centroids and old centroids are the same, 
#     break. Otherwise, start back at step 4 using our new centroids.


from colorsys import rgb_to_hsv
import random

import requests
from ColorController import ColorController
from ColorController.conversions import colorsys_hsv_to_hsv360, hsv360_to_hsvdistance
from ColorController.helpers import regular_round
from ColorController.namelookup import measure_hsv_distance
import numpy as np
from PIL import Image


def extract_colors(image_path, k=3, min_cycles=5, max_cycles=100, show_image=False, show_colors=False):
    """Use k-means algorithm to find dominant colors within a given image."""
    # 1.  Start with a collection of values. In this case, I am interested in
    #     rgb values, which are simplest to work with across image types.

    if not image_path[:4] == 'http':
        image_path = 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/25/An%C3%A9mona_de_mar_com%C3%BAn_%28Anemonia_viridis%29%2C_Parque_natural_de_la_Arr%C3%A1bida%2C_Portugal%2C_2020-07-21%2C_DD_07.jpg/500px-An%C3%A9mona_de_mar_com%C3%BAn_%28Anemonia_viridis%29%2C_Parque_natural_de_la_Arr%C3%A1bida%2C_Portugal%2C_2020-07-21%2C_DD_07.jpg'
    response = requests.get(image_path)
    print(image_path)
    if response.status_code == 200:
        image = Image.open(BytesIO(response.content)).convert("RGB")
        image.thumbnail((100, 100), Image.ANTIALIAS)
        if show_image:
            image.show()
        pixels = [(pix[0], pix[1], pix[2]) for pix in image.getdata()]

        # 2.  Select K positions (pixels) within the collection (pixel array),
        #     and find which seed position each other position in the collection
        #     is closest to (based on it's color using hsv distance). Label each
        #     position with that seed position.

        seed_indices = random.sample(range(len(pixels)), k)
        seeds = [pixels[i] for i in seed_indices]

        def label_pixel(pixel, seeds):
            """Measure the hsv distance between the given pixel and each seed, and return the seed (hsv) that is closest"""
            dists = {}
            for seed in seeds:
                dists[seed] = measure_hsv_distance(
                    hsv360_to_hsvdistance(colorsys_hsv_to_hsv360(rgb_to_hsv(*pixel))),
                    hsv360_to_hsvdistance(colorsys_hsv_to_hsv360(rgb_to_hsv(*seed)))
                )
            return min(dists.items(), key=lambda x: x[1])

        pixel_labels = {}
        for rgb in pixels:
            if rgb not in pixel_labels:
                pixel_labels[rgb] = label_pixel(rgb, seeds=seeds)

        # 3.  Take each sub-collection of lables, and calculate each of their
        #     averages (centroid). FIRST PASS.

        collections_a = {key: [] for key in seeds}
        for rgb in pixels:
            label = pixel_labels[rgb][0]
            collections_a[label].append(rgb)

        collections_a_centroids = {key: tuple(np.average(iter) for iter in zip(*val)) for key, val in
                                   collections_a.items()}

        def find_repr_points(collections, centroids):
            """
            Given a dictionary of collections and their centroids,
            return a dictionary of the closest points to each centroid.
            """
            repr_points = {v: None for k, v in centroids.items()}
            for label, pixel_collection in collections.items():
                for pixel in pixel_collection:
                    min_dist = 1
                    closest_pixel = ()
                    dist = measure_hsv_distance(
                        hsv360_to_hsvdistance(colorsys_hsv_to_hsv360(rgb_to_hsv(*centroids[label]))),
                        hsv360_to_hsvdistance(colorsys_hsv_to_hsv360(rgb_to_hsv(*pixel)))
                    )
                    if dist < min_dist:
                        closest_pixel, min_dist = pixel, dist
                repr_points[centroids[label]] = closest_pixel
            return repr_points

        # 4.  Take our set of k centroids, and for each member in our collection
        #     find which centroid it is closest to. Label it as such.

        pixel_labels = {}
        for rgb in pixels:
            if rgb not in pixel_labels:
                pixel_labels[rgb] = label_pixel(rgb, seeds=collections_a_centroids.values())

        # 5.  Take each sub-collection of labels, and calculate each of their
        #     averages (centroid). SECOND PASS.

        collections_b = {key: [] for key in collections_a_centroids.values()}
        for rgb in pixels:
            label = pixel_labels[rgb][0]
            collections_b[label].append(rgb)

        collections_b_centroids = {key: tuple(np.average(iter) for iter in zip(*val)) for key, val in
                                   collections_b.items()}

        # 6.  Compare new centroids to old centroids. If new centroids and old centroids are the same,
        #     break. Otherwise, start back at step 4 using our new centroids. LOOP UNTIL ANSWERED.
        def check_for_centroid_changes(centroids_a, centroids_b):
            for (r1, g1, b1), (r2, g2, b2) in zip(centroids_a, centroids_b):
                if not all([
                        (regular_round(r1) == regular_round(r2)),
                        (regular_round(g1) == regular_round(g2)),
                        (regular_round(b1) == regular_round(b2))]):
                    return False
            return True

        def check_for_repr_point_changes(repr_points_a, repr_points_b):
            """to be deprecated"""
            for (r1, g1, b1), (r2, g2, b2) in zip(repr_points_a, repr_points_b):
                if not all([r1 == r2, g1 == g2, b1 == b2]):
                    return False
            return True

        count = 0
        converged = False
        while (count < min_cycles) or (not converged and count < max_cycles):
            collections_a_centroids = collections_b_centroids
            pixel_labels = {}
            for rgb in pixels:
                if rgb not in pixel_labels:
                    pixel_labels[rgb] = label_pixel(rgb, seeds=collections_a_centroids.values())

            collections_b = {key: [] for key in collections_a_centroids.values()}
            for rgb in pixels:
                label = pixel_labels[rgb][0]
                collections_b[label].append(rgb)

            collections_b_centroids = {key: tuple(np.average(iter) for iter in zip(*val)) for key, val in
                                       collections_b.items()}

            converged = check_for_centroid_changes(collections_a_centroids.values(), collections_b_centroids.values())
            count += 1
            print(f"{count} of {max_cycles}")

        def measure_collection_inertia(collections):
            """
            Once convergence is reached, this function will measure
            the distance of each member of a collection from its centroid,
            and return the average distance for that collection.
            """
            collections_inertia = {}
            for centroid, members in collections.items():
                dists = []
                for member in members:
                    dist = measure_hsv_distance(
                        hsv360_to_hsvdistance(colorsys_hsv_to_hsv360(rgb_to_hsv(*centroid))),
                        hsv360_to_hsvdistance(colorsys_hsv_to_hsv360(rgb_to_hsv(*member)))
                    )
                    dists.append(dist)
                collections_inertia[centroid] = np.average(dists)
            return collections_inertia

        inertias = measure_collection_inertia(collections_b)
        avg_inertia = np.average([v for k, v in inertias.items()])

        dominant_colors = find_repr_points(collections_b, collections_b_centroids).values()
        if show_colors:
            for average_rgb in dominant_colors:
                color = ColorController(rgb=average_rgb)
                color.show_color()

        return avg_inertia, dominant_colors
