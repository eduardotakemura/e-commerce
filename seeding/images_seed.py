import os
import shutil
import random

def seed_images():
    """ Seeding script used to create and populate the products image folder with samples images. """
    # Directory path where folders will be created #
    base_dir = 'app/static/images/products/'

    # Sample image file path #
    sample_image_path = 'app/static/images/products/samples/'

    # Sample nutrition table file path #
    sample_nutritab_path = 'app/static/images/products/samples/nutri_table.png'

    # Number of product folders to create #
    starting_num = 51
    num_folders = 50

    for i in range(starting_num, starting_num + num_folders):
        # Create directory for each product ID
        product_dir = os.path.join(base_dir, str(i))
        os.makedirs(product_dir, exist_ok=True)

        random_sample = random.randint(1,8)
        full_sample_path = f"{sample_image_path}sample{random_sample}.png"

        # Copy the sample image to the new directory #
        shutil.copy(full_sample_path, os.path.join(product_dir, 'head.png'))
        shutil.copy(sample_nutritab_path, os.path.join(product_dir, 'nutrition.png'))

if __name__ == '__main__':
    seed_images()