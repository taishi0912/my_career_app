# 必要なライブラリのインポート
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
# Flask: Webアプリケーションフレームワーク
# render_template: HTMLテンプレートをレンダリングする関数
# request: クライアントからのリクエストを処理
# redirect, url_for: ページリダイレクト用
# session: ユーザーセッション管理
# flash: フラッシュメッセージ（一時的な通知）用
# jsonify: PythonオブジェクトをJSONレスポンスに変換

from flask_sqlalchemy import SQLAlchemy  # データベース操作用ORM
from sqlalchemy.orm import Session  # SQLAlchemyのセッション
import os  # ファイルパス操作用
from datetime import datetime, timedelta  # 日付と時間の操作
import json  # JSON形式のデータ処理
from collections import Counter  # 要素の出現回数をカウント
import logging  # ログ出力用
import random  # ランダムな値の生成

# ロギングの設定
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug("アプリケーションを開始します")

# Flaskアプリケーションの初期化
app = Flask(__name__)

# データベース設定
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # SQLiteデータベースを使用
app.config['SECRET_KEY'] = 'your_secret_key_here'  # セッション管理用の秘密鍵（本番環境では必ず変更すること）
db = SQLAlchemy(app)  # SQLAlchemyのインスタンスを作成

# ユーザーモデルの定義（データベーステーブルの構造）
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # 主キー
    username = db.Column(db.String(80), unique=True, nullable=False)  # ユーザー名
    password = db.Column(db.String(120), nullable=False)  # パスワード
    industry = db.Column(db.String(50), nullable=True)  # 業界
    aptitude_scores = db.Column(db.String(500), nullable=True)  # 適性スコア
    time_crystals = db.Column(db.Integer, default=0)  # タイムクリスタル数
    last_login = db.Column(db.DateTime, default=datetime.utcnow)  # 最終ログイン時間
    career_path = db.Column(db.String(500), default='[]')  # キャリアパス
    timeline = db.Column(db.String(1000), default='[]')  # タイムライン
    item_box = db.Column(db.String(500), default='[]')  # アイテムボックス

# キャリア選択の定義
# 各ステージでのユーザーの選択肢と次のステージへの遷移を定義
career_choices = {
    "start": {
        "question": "大学1年生の春、あなたはどんな活動を始めますか？",
        "choices": {
            "サークル活動に熱中する": {"next": "first_year_summer"},
            "アルバイトを始める": {"next": "first_year_summer"},
            "資格取得の勉強を始める": {"next": "first_year_summer"}
        }
    },
    "first_year_summer": {
        "question": "夏休みをどのように過ごしますか？",
        "choices": {
            "短期留学に参加": {"next": "first_year_fall"},
            "インターンシップに参加": {"next": "first_year_fall"},
            "旅行を楽しむ": {"next": "first_year_fall"}
        }
    },
    "first_year_fall": {
        "question": "秋学期、どの分野に興味を持ちましたか？",
        "choices": {
            "プログラミング": {"next": "first_year_winter"},
            "経済学": {"next": "first_year_winter"},
            "心理学": {"next": "first_year_winter"}
        }
    },
    "first_year_winter": {
        "question": "冬休みの過ごし方は？",
        "choices": {
            "ボランティア活動に参加": {"next": "second_year_spring"},
            "専門書を読み込む": {"next": "second_year_spring"},
            "アルバイトに集中": {"next": "second_year_spring"}
        }
    },
    "second_year_spring": {
        "question": "2年生になりました。どの授業に力を入れますか？",
        "choices": {
            "専門科目": {"next": "second_year_summer"},
            "教養科目": {"next": "second_year_summer"},
            "語学": {"next": "second_year_summer"}
        }
    },
    "second_year_summer": {
        "question": "夏休みの計画は？",
        "choices": {
            "長期インターンシップ": {"next": "career_choice_event"},
            "海外旅行": {"next": "career_choice_event"},
            "研究室訪問": {"next": "career_choice_event"}
        }
    },
    "career_choice_event": {
        "question": "重要な分岐点：将来のキャリアについて考える時期です。どの業界に興味がありますか？",
        "choices": {
            "IT・技術": {"next": "it_path"},
            "金融・ビジネス": {"next": "business_path"},
            "クリエイティブ・芸術": {"next": "creative_path"},
            "まだ決められない": {"next": "second_year_fall"}
        }
    },
    "it_path": {
        "question": "IT業界に興味を持ちました。どの分野を重点的に学びますか？",
        "choices": {
            "プログラミング": {"next": "second_year_fall"},
            "データサイエンス": {"next": "second_year_fall"},
            "ネットワーク": {"next": "second_year_fall"}
        }
    },
    "business_path": {
        "question": "ビジネス分野に興味を持ちました。どの領域を中心に学びますか？",
        "choices": {
            "マーケティング": {"next": "second_year_fall"},
            "財務・会計": {"next": "second_year_fall"},
            "経営戦略": {"next": "second_year_fall"}
        }
    },
    "creative_path": {
        "question": "クリエイティブ分野に興味を持ちました。どの領域を探求しますか？",
        "choices": {
            "デザイン": {"next": "second_year_fall"},
            "メディア制作": {"next": "second_year_fall"},
            "広告・PR": {"next": "second_year_fall"}
        }
    },
    "second_year_fall": {
        "question": "2年生の秋学期、どのような活動に注力しますか？",
        "choices": {
            "研究室の選択": {"next": "second_year_winter"},
            "課外プロジェクトへの参加": {"next": "second_year_winter"},
            "就職セミナーへの参加": {"next": "second_year_winter"}
        }
    },
    "second_year_winter": {
        "question": "冬休みの過ごし方は？",
        "choices": {
            "資格試験の勉強": {"next": "third_year_spring"},
            "卒業後の進路を考える": {"next": "third_year_spring"},
            "趣味や特技を深める": {"next": "third_year_spring"}
        }
    },
    "third_year_spring": {
        "question": "3年生になりました。この春学期の目標は？",
        "choices": {
            "GPA向上に集中": {"next": "third_year_summer"},
            "インターンシップの準備": {"next": "third_year_summer"},
            "課外活動でリーダーシップを発揮": {"next": "third_year_summer"}
        }
    },
    "third_year_summer": {
        "question": "就職活動が本格化する前の夏、何を優先しますか？",
        "choices": {
            "長期インターンシップ": {"next": "third_year_fall"},
            "海外留学": {"next": "third_year_fall"},
            "卒業研究の準備": {"next": "third_year_fall"}
        }
    },
    "third_year_fall": {
        "question": "就職活動の準備が始まります。どのように取り組みますか？",
        "choices": {
            "自己分析に集中": {"next": "third_year_winter"},
            "業界研究を徹底する": {"next": "third_year_winter"},
            "OB・OG訪問を積極的に行う": {"next": "third_year_winter"}
        }
    },
    "third_year_winter": {
        "question": "就職活動本番を前に、冬休みをどう過ごしますか？",
        "choices": {
            "エントリーシートの作成": {"next": "fourth_year_spring"},
            "面接対策を徹底する": {"next": "fourth_year_spring"},
            "卒業研究に集中": {"next": "fourth_year_spring"}
        }
    },
    "fourth_year_spring": {
        "question": "就職活動真っ只中の4年生。どのような戦略を取りますか？",
        "choices": {
            "大手企業を中心に応募": {"next": "fourth_year_summer"},
            "ベンチャー企業にチャレンジ": {"next": "fourth_year_summer"},
            "公務員試験に挑戦": {"next": "fourth_year_summer"}
        }
    },
    "fourth_year_summer": {
        "question": "就職活動も佳境に入りました。この夏の過ごし方は？",
        "choices": {
            "内定先が決まり、卒業旅行を楽しむ": {"next": "fourth_year_fall"},
            "最後の就職活動に全力を尽くす": {"next": "fourth_year_fall"},
            "卒業研究に専念する": {"next": "fourth_year_fall"}
        }
    },
    "fourth_year_fall": {
        "question": "進路が決まり、大学生活も残りわずか。この秋学期の目標は？",
        "choices": {
            "卒業に必要な単位を取得する": {"next": "fourth_year_winter"},
            "卒業論文の完成に向けて頑張る": {"next": "fourth_year_winter"},
            "後輩たちにアドバイスを与える": {"next": "fourth_year_winter"}
        }
    },
    "fourth_year_winter": {
        "question": "大学生活最後の冬。どのように締めくくりますか？",
        "choices": {
            "卒業式の準備と友人との思い出作り": {"next": "game_end"},
            "社会人としての心構えを固める": {"next": "game_end"},
            "最後の学生生活を満喫する": {"next": "game_end"}
        }
    },
    "game_end": {
        "question": "おめでとうございます！大学生活を終え、新たな人生の章が始まります。",
        "choices": {}
    }
}

# エンディングの定義
# ユーザーの選択によって到達する可能性のあるエンディングを定義
endings = {
    "tech_innovator": {
        "title": "テクノロジーイノベーター",
        "description": "あなたは革新的な技術で世界を変える立場になりました。",
        "required_choices": ["it_job", "programmer_path", "startup_path"]
    },
    "business_leader": {
        "title": "ビジネスリーダー",
        "description": "あなたは大企業のCEOとして、業界に大きな影響を与えています。",
        "required_choices": ["business_job", "corporate_path", "finance_path"]
    },
    "creative_entrepreneur": {
        "title": "クリエイティブ起業家",
        "description": "あなたの創造性と起業精神が、新しい産業を生み出しました。",
        "required_choices": ["creative_job", "startup_path", "marketing_path"]
    },
    "scientific_researcher": {
        "title": "科学研究者",
        "description": "あなたの研究が人類の知識の地平を押し広げました。",
        "required_choices": ["university", "engineering_job", "data_scientist_path"]
    },
    "social_impact_leader": {
        "title": "社会貢献リーダー",
        "description": "あなたは非営利組織を率いて、社会問題の解決に貢献しています。",
        "required_choices": ["vocational", "hospitality_job", "consultant_path"]
    }
}

# キャリア選択に追加の選択肢を加える
# これらは特定のキャリアパスを選択した後の、より詳細な選択肢を提供します
career_choices.update({
    "web_developer": {
        "question": "Web開発者としてのキャリアを選択しました。次のステップは？",
        "choices": {
            "フロントエンド専門": {"next": "game_end"},
            "バックエンド専門": {"next": "game_end"},
            "フルスタック開発": {"next": "game_end"}
        }
    },
    "mobile_developer": {
        "question": "モバイルアプリ開発者としてのキャリアを選択しました。次のステップは？",
        "choices": {
            "iOS開発": {"next": "game_end"},
            "Android開発": {"next": "game_end"},
            "クロスプラットフォーム開発": {"next": "game_end"}
        }
    },
    "game_developer": {
        "question": "ゲーム開発者としてのキャリアを選択しました。次のステップは？",
        "choices": {
            "コンソールゲーム開発": {"next": "game_end"},
            "モバイルゲーム開発": {"next": "game_end"},
            "VR/ARゲーム開発": {"next": "game_end"}
        }
    },
    # 他の最終選択肢も同様に追加予定
})

def init_db():
    """データベースを初期化する関数"""
    db_path = 'instance/users.db'
    if os.path.exists(db_path):
        os.remove(db_path)  # 既存のデータベースを削除
    with app.app_context():
        db.create_all()  # 新しいデータベースを作成
    print("データベースを初期化しました。")

def determine_aptitude(answers):
    """ユーザーの回答から適性を判断する関数"""
    industries = [
        "IT", "メーカー", "金融", "人材・教育", "専門・総合商社",
        "メディア・広告・マーケ", "コンサル・リサーチ", "インフラ", "不動産・建築", "サービス・小売"
    ]
    
    weights = [
        [2, 1, 1, 1, 1, 1, 1, 1, 1, 1],  # IT
        [1, 2, 1, 1, 1, 1, 1, 1, 1, 1],  # メーカー
        [1, 1, 2, 1, 1, 1, 1, 1, 1, 1],  # 金融
        [1, 1, 1, 2, 1, 1, 1, 1, 1, 1],  # 人材・教育
        [1, 1, 1, 1, 2, 1, 1, 1, 1, 1],  # 専門・総合商社
        [1, 1, 1, 1, 1, 2, 1, 1, 1, 1],  # メディア・広告・マーケ
        [1, 1, 1, 1, 1, 1, 2, 1, 1, 1],  # コンサル・リサーチ
        [1, 1, 1, 1, 1, 1, 1, 2, 1, 1],  # インフラ
        [1, 1, 1, 1, 1, 1, 1, 1, 2, 1],  # 不動産・建築
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 2],  # サービス・小売
    ]
    
    # 各回答に微小なランダム値を加える
    answers_with_noise = [a + random.uniform(0, 0.1) for a in answers]
    
    # スコアを計算
    scores = [sum([a * w for a, w in zip(answers_with_noise, industry_weights)]) for industry_weights in weights]
    
    # 最大スコアを持つ業界のインデックスを取得
    max_score_indices = [i for i, score in enumerate(scores) if score == max(scores)]
    
    # 最大スコアの業界が複数ある場合、ランダムに1つ選択
    max_score_index = random.choice(max_score_indices)
    
    # 選択された業界以外のスコアを調整
    adjusted_scores = []
    for i, score in enumerate(scores):
        if i == max_score_index:
            adjusted_scores.append(score)
        else:
            # 最大スコアの95%～99%の範囲でランダムに調整
            adjusted_scores.append(score * random.uniform(0.95, 0.99))
    
    # スコアを正規化（0-100の範囲に収める）
    max_adjusted_score = max(adjusted_scores)
    normalized_scores = [int((score / max_adjusted_score) * 100) for score in adjusted_scores]
    
    aptitude_scores = dict(zip(industries, normalized_scores))
    best_industry = industries[max_score_index]
    
    return best_industry, aptitude_scores

def update_login_bonus(user):
    """ユーザーのログインボーナスを更新する関数"""
    today = datetime.utcnow().date()
    last_login = user.last_login.date() if user.last_login else None
    
    if last_login != today:
        user.time_crystals += 1  # 毎日のログインボーナス
        if last_login == today - timedelta(days=1):
            consecutive_days = (today - user.last_login.date()).days + 1
            if consecutive_days % 7 == 0:
                user.time_crystals += 2  # 週間ボーナス
            if consecutive_days % 30 == 0:
                user.time_crystals += 5  # 月間ボーナス
        user.last_login = datetime.utcnow()
        db.session.commit()
        flash(f'ログインボーナスとして{user.time_crystals}個のタイムクリスタルを獲得しました！', 'success')

def get_next_choice(current_state):
    """
    現在の状態から次の選択肢を取得する関数
    
    :param current_state: 現在のゲーム状態
    :return: 次の選択肢の辞書、またはゲーム終了状態
    """
    next_choice = career_choices.get(current_state, {
        "question": "このキャリアパスは終了しました。",
        "choices": {}
    })
    
    # 選択肢がない場合は game_end 状態を返す
    if not next_choice['choices']:
        return career_choices["game_end"]
    
    return next_choice

def calculate_time_crystal_cost(choice):
    """
    選択に応じたタイムクリスタルのコストを計算する関数
    
    :param choice: ユーザーの選択
    :return: タイムクリスタルのコスト
    """
    important_choices = ['university', 'job_change', 'promotion']
    return 3 if choice in important_choices else 1

def evaluate_career(career_path):
    """
    キャリアパスを評価する関数
    
    :param career_path: ユーザーのキャリアパス
    :return: キャリアの評価結果（文字列）
    """
    if not career_path:
        return "まだ始まったばかりの"

    unique_choices = len(set(career_path))
    path_length = len(career_path)
    
    if path_length == 0:
        return "これから始まる"
    
    diversity_ratio = unique_choices / path_length
    
    if diversity_ratio > 0.7:
        return "多様な経験を積んだ"
    elif diversity_ratio < 0.3:
        return "専門性の高い"
    else:
        return "バランスの取れた"

def determine_ending(career_path):
    """
    キャリアパスに基づいてエンディングを決定する関数
    
    :param career_path: ユーザーのキャリアパス
    :return: エンディングの種類（文字列）
    """
    path_counter = Counter(career_path)
    
    for ending, data in endings.items():
        if all(choice in career_path for choice in data["required_choices"]):
            return ending
    
    # デフォルトエンディング
    return "balanced_professional"
#################################めも
@app.route('/')
def home():
    """ホームページを表示するルート"""
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    ユーザー登録を処理するルート
    GET: 登録フォームを表示
    POST: 登録処理を実行
    """
    questions = [
        "新しい技術やツールを学ぶことにワクワクしますか？",
        "ものづくりや製品開発に興味がありますか？",
        "数字を扱うことや金融市場に関心がありますか？",
        "人を教えたり、サポートしたりすることが好きですか？",
        "多様な商品やサービスを扱うことに興味がありますか？",
        "創造的な仕事や表現活動に関心がありますか？",
        "データ分析や問題解決に興味がありますか？",
        "大規模なシステムや設備の管理に関心がありますか？",
        "空間デザインや建築に興味がありますか？",
        "顧客サービスや接客に関心がありますか？"
    ]
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        answers = [int(request.form[f'q{i}']) for i in range(1, 11)]
        industry, aptitude_scores = determine_aptitude(answers)
        pass
    
        new_user = User(
            username=username,
            password=password,
            industry=industry,
            aptitude_scores=json.dumps(aptitude_scores),
            time_crystals=1  # 新規登録時に1個のタイムクリスタルを配布
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash('新規登録キャンペーン!タイムクリスタル1個配布中!', 'success')
        return render_template('registration_result.html', industry=industry, aptitude_scores=aptitude_scores)
    
    return render_template('register.html', questions=questions)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    ログインを処理するルート
    GET: ログインフォームを表示
    POST: ログイン処理を実行
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            update_login_bonus(user)
            return redirect(url_for('game'))
        else:
            flash('ユーザー名またはパスワードが間違っています。', 'error')
    return render_template('login.html')

@app.route('/game')
def game():
    """
    ゲームのメインページを表示するルート
    ユーザーの現在の状態を取得し、次の選択肢を提示する
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = db.session.get(User, session['user_id'])
    if not user:
        flash('ユーザーが見つかりません。', 'error')
        return redirect(url_for('login'))
    
    career_path = json.loads(user.career_path)
    current_state = career_path[-1] if career_path else "start"
    next_choice = get_next_choice(current_state)
    
    can_go_back = len(career_path) > 1 and user.time_crystals > 0
    
    if not next_choice['choices']:
        return redirect(url_for('game_over'))
    
    choices = list(next_choice['choices'].keys())
    
    return render_template('game.html', user=user, career_path=career_path, 
                           next_question=next_choice['question'], choices=choices,
                           can_go_back=can_go_back)

@app.route('/make_choice', methods=['POST'])
def make_choice():
    """
    ユーザーの選択を処理するルート
    選択に基づいてキャリアパスを更新し、次の状態に進む
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    choice = request.form['choice']
    
    career_path = json.loads(user.career_path)
    current_state = career_path[-1] if career_path else "start"
    
    next_choice = get_next_choice(current_state)
    if choice not in next_choice['choices']:
        flash('無効な選択です。', 'error')
        return redirect(url_for('game'))

    next_state = next_choice['choices'][choice]['next']
    career_path.append(next_state)
    user.career_path = json.dumps(career_path)
    
    # タイムラインに新しい選択を追加
    timeline = json.loads(user.timeline)
    timeline.append({
        'state': next_state,
        'question': next_choice['question'],
        'choice': choice,
        'timestamp': datetime.utcnow().isoformat(),
        'crystals_used': 0,
        'is_important': current_state == "career_choice_event"  # 重要な分岐点かどうか
    })
    user.timeline = json.dumps(timeline)

    db.session.commit()
    flash('新しい選択をしました！', 'success')

    # ゲーム終了条件のチェック
    if next_state == "game_end" or len(career_path) >= 10 or not get_next_choice(next_state)['choices']:
        return redirect(url_for('game_over'))

    return redirect(url_for('game'))

@app.route('/use_time_crystal', methods=['POST'])
def use_time_crystal():
    """
    タイムクリスタルを使用して前の選択に戻る処理を行うルート
    """
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "ログインしていません。"})

    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({"success": False, "message": "ユーザーが見つかりません。"})

    career_path = json.loads(user.career_path)
    if len(career_path) <= 1:
        return jsonify({"success": False, "message": "これ以上前に戻れません。"})

    cost = calculate_time_crystal_cost(career_path[-1])
    if user.time_crystals < cost:
        return jsonify({"success": False, "message": f"タイムクリスタルが足りません。必要数: {cost}"})

    # 重要な分岐点まで戻る
    while career_path and not is_important_choice(career_path[-1]):
        career_path.pop()

    if not career_path:
        return jsonify({"success": False, "message": "重要な分岐点が見つかりません。"})

    user.time_crystals -= cost
    user.career_path = json.dumps(career_path)
    
    # タイムラインにタイムクリスタル使用を記録
    timeline = json.loads(user.timeline)
    timeline.append({
        'state': 'タイムクリスタル使用',
        'timestamp': datetime.utcnow().isoformat(),
        'crystals_used': cost
    })
    user.timeline = json.dumps(timeline)
    
    db.session.commit()
    return jsonify({"success": True, "message": "重要な分岐点に戻りました。"})

def is_important_choice(state):
    # 重要な分岐点かどうかを判断するロジック
    important_states = ["career_choice_event", "university", "first_job"]
    return state in important_states

######################めも印

@app.route('/timeline')
def timeline():
    """
    ユーザーのタイムラインを表示するルート
    
    ユーザーのこれまでの選択履歴を時系列で表示する
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        flash('ユーザーが見つかりません。', 'error')
        return redirect(url_for('login'))
    
    timeline = json.loads(user.timeline)
    return render_template('timeline.html', user=user, timeline=timeline)

@app.route('/api/timeline')
def api_timeline():
    """
    タイムラインデータを提供するAPIエンドポイント
    
    フロントエンド側でタイムラインを動的に更新する際に使用する
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    timeline = json.loads(user.timeline)
    return jsonify(timeline)

@app.route('/go_back', methods=['POST'])
def go_back():
    """
    前の選択に戻る機能を提供するルート
    
    タイムクリスタルを消費して、キャリアパスの最後の選択を取り消す
    """
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "ログインしていません。"}), 401

    user = db.session.get(User, session['user_id'])
    if not user:
        return jsonify({"success": False, "message": "ユーザーが見つかりません。"}), 404

    career_path = json.loads(user.career_path)
    if len(career_path) <= 1:
        return jsonify({"success": False, "message": "これ以上前に戻れません。"}), 400

    if user.time_crystals < 1:
        return jsonify({"success": False, "message": "タイムクリスタルが足りません。"}), 400

    # タイムクリスタルを消費
    user.time_crystals -= 1

    # 前の選択に戻る
    career_path.pop()
    user.career_path = json.dumps(career_path)

    # タイムラインに「戻る」アクションを記録
    timeline = json.loads(user.timeline)
    timeline.append({
        'state': '前の選択に戻る',
        'timestamp': datetime.utcnow().isoformat(),
        'crystals_used': 1
    })
    user.timeline = json.dumps(timeline)

    # データベースの変更を保存
    db.session.commit()

    return jsonify({"success": True, "message": "前の選択に戻りました。"}), 200

@app.route('/game_over')
def game_over():
    """
    ゲーム終了画面を表示するルート
    ユーザーのキャリアパスを評価し、結果を表示する
    """
    if 'user_id' not in session:
        flash('セッションが切れました。再度ログインしてください。', 'error')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if user is None:
        flash('ユーザーが見つかりません。', 'error')
        return redirect(url_for('login'))
    
    career_path = json.loads(user.career_path)
    timeline = json.loads(user.timeline)
    item_box = json.loads(user.item_box)
    
    user_type = determine_type(career_path)
    ending = determine_ending(career_path)
    evaluation = evaluate_career(career_path)
    unique_choices_count = len(set(career_path))
    
    return render_template('game_over.html', 
                           user=user,
                           user_type=user_type,
                           ending=ending,
                           evaluation=evaluation,
                           career_path=career_path,
                           timeline=timeline,
                           item_box=item_box,
                           unique_choices_count=unique_choices_count)


def determine_type(career_path):
    # ユーザータイプを決定するロジックをここに実装
    # 仮の実装として、最後の選択を返す
    return career_path[-1] if career_path else "未定義"

def determine_ending(career_path):
    # エンディングを決定するロジックをここに実装
    # 仮の実装
    return {
        "title": "キャリアの終着点",
        "description": "あなたは素晴らしいキャリアを築き上げました。"
    }

def evaluate_career(career_path):
    # キャリアを評価するロジックをここに実装
    # 仮の実装
    return "バランスの取れた"

@app.route('/force_game_over')
def force_game_over():
    """
    ゲームを強制的に終了するルート
    デバッグや特定の状況で使用
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    career_path = json.loads(user.career_path)
    career_path.append("game_end")
    user.career_path = json.dumps(career_path)
    db.session.commit()
    
    flash('ゲームを強制終了しました。', 'info')
    return redirect(url_for('game_over'))

@app.route('/future_self_analysis', methods=['POST'])
def perform_future_self_analysis():
    """
    未来の自己分析を行う処理のルート
    ユーザーのキャリアパスに基づいて分析結果を生成
    """
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    user = db.session.get(User, session['user_id'])
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    career_path = json.loads(user.career_path)
    
    # 分析ロジック（仮実装）
    analysis = {
        "strength": "適応力と柔軟性",
        "weakness": "長期的な計画立案",
        "opportunity": "新しい技術スキルの習得",
        "threat": "急速に変化する業界トレンド"
    }
    app.logger.info(f"Future self analysis performed for user {user.id}")  # ログ追加
    return jsonify(analysis)

@app.route('/get_ai_response', methods=['POST'])
def generate_ai_response():
    """
    AI応答を生成する処理のルート
    ユーザーの質問に対して、キャリアパスに基づいた回答を生成する
    この機能は未来の自分との対話をシミュレートする
    """
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    user = db.session.get(User, session['user_id'])
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    question = request.form['question']
    
    # AI応答ロジック（仮実装）
    # 実際のAI機能を実装する際は、より高度な自然言語処理や機械学習モデルを使用する予定です
    response = f"あなたの質問 '{question}' に対する未来の自分からの回答: 技術の世界は常に変化しています。新しいスキルを学び続けることが重要です。"
    
    return jsonify({"response": response})

# アプリケーションのメイン関数
if __name__ == '__main__':
    print("アプリケーションを初期化しています...")
    try:
        # データベースの初期化
        init_db()
        print("データベースが初期化されました。")
    except Exception as e:
        print(f"データベースの初期化中にエラーが発生しました: {str(e)}")
    
    print("Flaskアプリケーションを起動しています...")
    # デバッグモードでアプリケーションを実行
    # ポート5001で起動（デフォルトのFlaskポートは5000）
    app.run(debug=True, port=5001)
    print("アプリケーションが終了しました。")