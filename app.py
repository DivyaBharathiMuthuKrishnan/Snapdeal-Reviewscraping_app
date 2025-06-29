from flask import Flask, render_template, request
import pandas as pd
import os
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from snapdeal_scraper import scrape_snapdeal_reviews

app = Flask(__name__)
scraped_reviews = []  # store reviews in memory

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/result', methods=['POST'])
def result():
    global scraped_reviews

    # Get form data
    product_url = request.form['product_url']
    pages_str = request.form.get('pages', '5').strip()
    try:
        pages = int(pages_str)
        if pages < 1:
            pages = 5
    except ValueError:
        pages = 5

    # Scrape reviews
    scraped_reviews = scrape_snapdeal_reviews(product_url, pages=pages, delay=2)

    if not scraped_reviews:
        return render_template('result.html', message="❌ No reviews found or scraping failed.", reviews=[])

    # Save to CSV
    df = pd.DataFrame(scraped_reviews)
    csv_path = os.path.join(os.getcwd(), 'snapdeal_reviews.csv')
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')

    # Word Cloud
    all_text = " ".join(df['review_text'].dropna())
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(all_text)
    image_path = os.path.join('static', 'wordcloud.png')
    wordcloud.to_file(image_path)

    return render_template('result.html',
                           message=f"✅ Scraped {len(scraped_reviews)} reviews!",
                           reviews=scraped_reviews,
                           image_url=image_path)

@app.route('/analyze', methods=['POST'])
def analyze():
    global scraped_reviews

    if not scraped_reviews:
        return render_template('result.html', message="❌ No reviews found to analyze.", reviews=[])

    # Split by ratings
    happy = [r for r in scraped_reviews if r.get('rating') and r['rating'] >= 4]
    neutral = [r for r in scraped_reviews if r.get('rating') == 3]
    unhappy = [r for r in scraped_reviews if r.get('rating') and r['rating'] <= 2]

    total_reviews = len([r for r in scraped_reviews if r.get('rating')])
    if total_reviews == 0:
        happy_pct = neutral_pct = unhappy_pct = 0
    else:
        happy_pct = round(100 * len(happy) / total_reviews, 2)
        neutral_pct = round(100 * len(neutral) / total_reviews, 2)
        unhappy_pct = round(100 * len(unhappy) / total_reviews, 2)

    # Average rating
    ratings = [r['rating'] for r in scraped_reviews if r.get('rating') is not None]
    avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else "N/A"

    # Expected improvement if addressing unhappy customers
    potential_increase = unhappy_pct * 0.6
    improved_happy = happy_pct + potential_increase
    if improved_happy > 100:
        improved_happy = 100
    improved_happy = round(improved_happy, 2)

    # Recommendations
    recommendations = [
        "Improve delivery time",
        "Add accurate color photos",
        "Improve fabric quality",
        "Ensure better packaging",
        "Accurate sizing and descriptions"
    ]

    # Pie Chart
    labels = ['Happy (4-5)', 'Neutral (3)', 'Unhappy (1-2)']
    sizes = [len(happy), len(neutral), len(unhappy)]
    colors = ['#4CAF50', '#FFC107', '#F44336']

    plt.figure(figsize=(6,6))
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
    plt.title('Customer Sentiment Distribution')
    pie_path = os.path.join('static', 'satisfaction_pie.png')
    plt.savefig(pie_path)
    plt.close()

    # Bar Chart
    rating_counts = {}
    for i in range(1, 6):
        rating_counts[i] = sum(1 for r in scraped_reviews if r.get('rating') == i)

    plt.figure(figsize=(8,5))
    plt.bar(rating_counts.keys(), rating_counts.values(), color='#2196F3')
    plt.xlabel('Rating')
    plt.ylabel('Number of Reviews')
    plt.title('Number of Reviews per Rating')
    plt.xticks([1, 2, 3, 4, 5])
    bar_path = os.path.join('static', 'ratings_bar.png')
    plt.savefig(bar_path)
    plt.close()

    return render_template(
        'analysis.html',
        avg_rating=avg_rating,
        total_reviews=total_reviews,
        happy_pct=happy_pct,
        improved_happy=improved_happy,
        recommendations=recommendations,
        pie_image=pie_path,
        bar_image=bar_path
    )

if __name__ == "__main__":
    app.run(debug=True)

