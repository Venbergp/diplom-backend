import os

from flask import Blueprint, request, jsonify, current_app, send_file
from PIL import Image
import io
from datetime import datetime
from flask import jsonify
from bson.objectid import ObjectId
import random
from surprise import dump

profile = Blueprint('profile', __name__)


@profile.route('/<user_id>', methods=['GET'])
def get_profile(user_id):
    users = current_app.mongo.db.users
    products = current_app.mongo.db.products
    user = users.find_one({"_id": ObjectId(user_id)})

    if not user:
        return jsonify({"error": "User not found"}), 404

    # Извлекаем все продукты, связанные с этим пользователем
    product_ids = [str(product['_id']) for product in products.find({"user_id": ObjectId(user_id)})]

    profile_info = {
        "username": user["username"],
        "product_ids": product_ids[::-1]
    }

    return jsonify(profile_info), 200

#получение username
@profile.route('/get_username/<user_id>', methods=['GET'])
def get_username(user_id):
    users = current_app.mongo.db.users
    user = users.find_one({"_id": ObjectId(user_id)})

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"user_id": user_id, "username": user['username']}), 200

# Форматирование картинки
@profile.route('/apply_print', methods=['POST'])
def apply_print():
    if 'print' not in request.files:
        return jsonify({"error": "No print file provided"}), 400

    print_file = request.files['print']
    if print_file:
        tshirt_image = Image.open('app\\sample\\white_t-shirt.jpg').convert('RGBA')
        print_image = Image.open(print_file.stream).convert('RGBA')
        print_image = print_image.resize((400, 400))

        tshirt_width, tshirt_height = tshirt_image.size
        print_width, print_height = print_image.size
        position = (
            (tshirt_width - print_width) // 2,
            (tshirt_height - print_height) // 2 - 200
        )

        tshirt_image.paste(print_image, position, print_image)

        img_byte_arr = io.BytesIO()
        tshirt_image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        return send_file(
            img_byte_arr,
            as_attachment=True,
            download_name='custom_tshirt.png',
            mimetype='image/png'
        )

    return jsonify({"error": "Invalid file"}), 400


# Опубликование поста
@profile.route('/post', methods=['POST'])
def create_post():
    user_id = request.form.get('user_id')
    caption = request.form.get('caption')

    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400

    image_file = request.files['image']
    if not image_file:
        return jsonify({"error": "Invalid image"}), 400

    users = current_app.mongo.db.users
    user = users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"error": "User not found"}), 404

    image_path = f"uploads/{ObjectId()}.png"
    image_file.save(image_path)

    posts = current_app.mongo.db.posts
    post_id = posts.insert_one({
        "user_id": ObjectId(user_id),
        "caption": caption,
        "image_path": image_path,
        "created_at": datetime.utcnow(),
        "liked_by_users": []
    }).inserted_id

    return jsonify({"message": "Post created successfully", "post_id": str(post_id)}), 201


# Получение списка постов
@profile.route('/user_posts/<user_id>', methods=['GET'])
def get_user_posts(user_id):
    # Проверяем, существует ли пользователь
    users = current_app.mongo.db.users
    user = users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Извлекаем все посты, связанные с этим пользователем
    posts = current_app.mongo.db.posts
    user_posts = posts.find({"user_id": ObjectId(user_id)})

    # Собираем список ID постов
    post_ids = [str(post['_id']) for post in user_posts]

    return jsonify({"user_id": user_id, "post_ids": post_ids[::-1]}), 200


# Отправка информации поста
@profile.route('/post_details/<post_id>', methods=['GET'])
def get_post_details(post_id):
    posts = current_app.mongo.db.posts
    post = posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        return jsonify({"error": "Post not found"}), 404

    users = current_app.mongo.db.users
    user = users.find_one({"_id": ObjectId(post['user_id'])})
    if not user:
        return jsonify({"error": "User not found"}), 404
    print(post)
    post_details = {
        "username": user['username'],
        "caption": post['caption'],
        "image_path": post['image_path'],
        "likes_count": len(post['liked_by_users'])
    }

    return jsonify(post_details), 200


# Отправка картинки поста
@profile.route('/post_image/<post_id>', methods=['GET'])
def get_post_image(post_id):
    posts = current_app.mongo.db.posts
    post = posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        return jsonify({"error": "Post not found"}), 404

    image_path = '..\\' + post['image_path'].replace('/', '\\')
    return send_file(image_path, mimetype='image/png', as_attachment=True, download_name='post_image.png')


@profile.route('/like_post', methods=['POST'])
def like_post():
    data = request.get_json()
    user_id = data.get('user_id')
    post_id = data.get('post_id')

    if not user_id or not post_id:
        return jsonify({"error": "User ID and Post ID are required"}), 400

    users = current_app.mongo.db.users
    user = users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"error": "User not found"}), 404

    posts = current_app.mongo.db.posts
    post = posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        return jsonify({"error": "Post not found"}), 404

    result = posts.update_one(
        {"_id": ObjectId(post_id)},
        {"$addToSet": {"liked_by_users": ObjectId(user_id)}}
    )

    if result.modified_count > 0:
        return jsonify({"message": "Like added successfully"}), 200
    else:
        return jsonify({"message": "Like was already added"}), 200


@profile.route('/unlike_post', methods=['POST'])
def unlike_post():
    data = request.get_json()
    user_id = data.get('user_id')
    post_id = data.get('post_id')

    if not user_id or not post_id:
        return jsonify({"error": "User ID and Post ID are required"}), 400

    users = current_app.mongo.db.users
    user = users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"error": "User not found"}), 404

    posts = current_app.mongo.db.posts
    post = posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        return jsonify({"error": "Post not found"}), 404

    result = posts.update_one(
        {"_id": ObjectId(post_id)},
        {"$pull": {"liked_by_users": ObjectId(user_id)}}
    )

    if result.modified_count > 0:
        return jsonify({"message": "Like removed successfully"}), 200
    else:
        return jsonify({"message": "Like was not present"}), 200


@profile.route('/check_like/<post_id>/<user_id>', methods=['GET'])
def check_like(post_id, user_id):
    # Проверяем существование поста
    posts = current_app.mongo.db.posts
    post = posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        return jsonify({"error": "Post not found"}), 404

    # Проверяем, лайкнул ли пользователь пост
    user_liked = ObjectId(user_id) in post.get('liked_by_users', [])

    return jsonify({"userLiked": user_liked}), 200


# @profile.route('/recommendations/<user_id>', methods=['GET'])
# def get_recommendations(user_id):
#     posts = current_app.mongo.db.posts
#     all_posts = list(posts.find({}))
#
#     # Проверяем существование пользователя
#     users = current_app.mongo.db.users
#     user = users.find_one({"_id": ObjectId(user_id)})
#     if not user:
#         return jsonify({"error": "User not found"}), 404
#
#     # Выбираем случайные 10 постов
#     recommended_posts = random.sample(all_posts, min(10, len(all_posts)))
#
#     # Формируем ответ с ID постов
#     recommended_post_ids = [str(post['_id']) for post in recommended_posts]
#     return jsonify({"recommended_post_ids": recommended_post_ids}), 200


# Загружаем модель из файла


@profile.route('/recommendations/<user_id>', methods=['GET'])
def recommend_new_items(user_id):
    _, model = dump.load('app/recommendation_system/models/recommendation_model.pkl')
    posts = current_app.mongo.db.posts

    all_items = [str(post['_id']) for post in posts.find({}, {"_id": 1})]

    known_items = [str(post['_id']) for post in posts.find({"liked_by_users": user_id}, {"_id": 1})]

    unknown_items = list(set(all_items) - set(known_items))

    predictions = {}
    for item_id in unknown_items:
        pred = model.predict(user_id, item_id)
        predictions[item_id] = pred.est

    sorted_predictions = [x[0] for x in sorted(predictions.items(), key=lambda x: x[1], reverse=True)]

    print(sorted_predictions)
    return jsonify({"recommended_post_ids": sorted_predictions})



@profile.route('/profile_stats/<user_id>', methods=['GET'])
def get_profile_stats(user_id):
    users = current_app.mongo.db.users
    posts = current_app.mongo.db.posts

    # Check if the user exists
    user = users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Calculate the total number of works
    total_works = posts.count_documents({"user_id": ObjectId(user_id)})

    # Calculate the total number of likes
    user_posts = posts.find({"user_id": ObjectId(user_id)})
    total_likes = sum(len(post.get('liked_by_users', [])) for post in user_posts)

    # Mock the number of sales
    total_sales = random.randint(0, total_likes)

    return jsonify({
        "total_works": total_works,
        "total_likes": total_likes,
        "total_sales": total_sales
    }), 200
