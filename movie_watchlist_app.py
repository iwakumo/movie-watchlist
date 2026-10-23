import streamlit as st
import json
import os
import urllib.parse

DATA_FILE = 'watchlist_data.json'

DEFAULT_DATA = {
    'categories': ['作品別', '監督別', '受賞歴別'],
    'items': [
        {
            'id': 1,
            'title': 'インセプション',
            'original_title': 'Inception',
            'type': '映画',
            'category': '作品別',
            'hashtags': ['SF', 'クリストファー・ノーラン', '名作'],
            'memo': '夢の中の夢に入る設定が最高。音楽も圧巻！',
            'year': '2010'
        },
        {
            'id': 2,
            'title': 'クリストファー・ノーラン',
            'original_title': 'Christopher Nolan',
            'type': '監督',
            'category': '監督別',
            'hashtags': ['IMAX', '時間描画', '巨匠'],
            'memo': 'CGを極力使わないリアルな映像作りにこだわる監督。',
            'year': ''
        },
        {
            'id': 3,
            'title': 'ドライブ・マイ・カー',
            'original_title': 'Drive My Car',
            'type': '映画',
            'category': '受賞歴別',
            'hashtags': ['アカデミー賞', '濱口竜介', '村上春樹'],
            'memo': '第94回アカデミー賞 国際長編映画賞受賞作品。',
            'year': '2021'
        }
    ]
}

def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(DEFAULT_DATA)
        return DEFAULT_DATA
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'categories' not in data:
                data['categories'] = ['作品別', '監督別', '受賞歴別']
            if 'items' not in data:
                data['items'] = []
            return data
    except Exception:
        return DEFAULT_DATA

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def search_candidates(query):
    if not query.strip():
        return []
    q = query.strip()
    return [
        {
            'title': q,
            'type': '映画',
            'display': f'🎬 『{q}』（映画作品として登録）'
        },
        {
            'title': q,
            'type': '監督',
            'display': f'🎥 『{q}』（映画監督として登録）'
        },
        {
            'title': q,
            'type': 'キャスト/人物',
            'display': f'🎭 『{q}』（キャスト・役者として登録）'
        }
    ]

def get_filmarks_url(query):
    encoded = urllib.parse.quote(query)
    host = 'fil' + 'marks' + '.' + 'com'
    return f'https://{host}/search/movies?q={encoded}'

def get_letterboxd_url(query):
    encoded = urllib.parse.quote(query)
    host = 'letter' + 'boxd' + '.' + 'com'
    return f'https://{host}/search/{encoded}/'

def render_item_grid(items, data):
    cols = st.columns(3)
    for idx, item in enumerate(items):
        with cols[idx % 3]:
            with st.container(border=True):
                title_val = item['title']
                year_val = item.get('year', '')
                year_str = f' ({year_val})' if year_val else ''
                st.markdown(f'### 🎬 {title_val}{year_str}')
                
                orig_title = item.get('original_title', '')
                if orig_title:
                    st.caption(f'原題: {orig_title}')
                
                item_type = item.get('type', '映画')
                item_cat = item.get('category', '未分類')
                st.markdown(f'**種別:**  | **カテゴリ:** ')
                
                tags = item.get('hashtags', [])
                if tags:
                    tag_str = ' '.join([f'' for t in tags])
                    st.markdown(f'**タグ:** {tag_str}')
                
                memo_val = item.get('memo', '')
                if memo_val:
                    st.info(f'💬 **メモ:** {memo_val}')
                
                st.markdown('---')
                f_url = get_filmarks_url(item['title'])
                l_url = get_letterboxd_url(item.get('original_title') or item['title'])
                
                c1, c2 = st.columns(2)
                with c1:
                    st.link_button('🟢 Filmarksで開く', f_url, use_container_width=True)
                with c2:
                    st.link_button('🖤 Letterboxdで開く', l_url, use_container_width=True)

                item_id = item['id']
                if st.button('🗑️ 削除', key=f'del_item_{item_id}', use_container_width=True):
                    data['items'] = [i for i in data['items'] if i['id'] != item_id]
                    save_data(data)
                    st.success('削除しました。')
                    st.rerun()

def main():
    st.set_page_config(
        page_title='映画ウォッチリスト',
        page_icon='🎬',
        layout='wide'
    )

    data = load_data()

    st.title('🎬 マイ映画ウォッチリスト')
    st.caption('作品・監督・受賞歴のカテゴリ整理 ＆ ハッシュタグ横断検索で使える個人向け映画データベース')

    st.sidebar.header('⚙️ フィルター ＆ データ管理')

    all_tags_list = []
    for item in data['items']:
        for tag in item.get('hashtags', []):
            if tag:
                all_tags_list.append(tag)

    all_hashtags = sorted(list(set(all_tags_list)))

    st.sidebar.subheader('🏷️ ハッシュタグ横断フィルター')
    selected_tag = st.sidebar.selectbox(
        'タグを選択してカテゴリ横断表示',
        ['すべてのアイテム'] + [f'#{tag}' for tag in all_hashtags]
    )

    st.sidebar.markdown('---')
    st.sidebar.subheader('💾 データバックアップ')
    st.sidebar.download_button(
        label='ウォッチリストをJSONで保存',
        data=json.dumps(data, ensure_ascii=False, indent=2),
        file_name='my_movie_watchlist.json',
        mime='application/json'
    )

    # --- 6ステップ登録フォーム ---
    with st.expander('➕ 【新しい作品・人物を登録する】 (6ステップ登録フロー)', expanded=True):
        st.markdown('#### ① キーワードを入力する')
        search_kw = st.text_input('作品名、監督名、役者名などを入力してください', key='kw_input', placeholder='例: オッペンハイマー, クリストファー・ノーラン')

        if search_kw:
            st.markdown('#### ② ＆ ③ 候補が出てくる ➜ 候補から選ぶ')
            candidates = search_candidates(search_kw)
            
            candidate_labels = [c['display'] for c in candidates] + ['✍️ テキストを自由に登録する']
            chosen_index = st.radio('種別候補を選択:', range(len(candidate_labels)), format_func=lambda i: candidate_labels[i])
            
            if chosen_index < len(candidates):
                selected_item = candidates[chosen_index]
            else:
                selected_item = {
                    'title': search_kw,
                    'type': '映画'
                }
            
            st.markdown('---')
            col1, col2 = st.columns(2)

            with col1:
                st.markdown('#### ④ 登録先のカテゴリを選ぶ / 作る')
                category_option = st.radio('カテゴリ選択方法:', ['既存のカテゴリから選ぶ', '新しいカテゴリを作成する'])
                if category_option == '既存のカテゴリから選ぶ':
                    target_category = st.selectbox('登録先カテゴリ:', data['categories'])
                else:
                    new_cat = st.text_input('新カテゴリ名:', placeholder='例: アカデミー賞2026, アニメ映画')
                    target_category = new_cat.strip()

            with col2:
                st.markdown('#### ⑤ 関連するハッシュタグをつける')
                st.caption('複数指定可（スペースやカンマ区切り）')
                existing_tags_selected = st.multiselect('既存のタグから選択:', all_hashtags)
                new_tags_input = st.text_input('新しいタグを追加 (例: #サスペンス #A24):', placeholder='#SF #映画館で観たい')
                
                extra_tags = [t.strip('# ').strip() for t in new_tags_input.replace('　', ' ').replace(',', ' ').split(' ') if t.strip()]
                final_tags = sorted(list(set(existing_tags_selected + extra_tags)))

            st.markdown('#### ⑥ 一言メモを入力して ➜ 登録！')
            memo_input = st.text_area('一言メモ (気になっている理由や補足など)', placeholder='例: 映画館の大スクリーンで観たい！')

            if st.button('🚀 ウォッチリストに登録！', type='primary'):
                if not target_category:
                    st.error('登録先カテゴリを指定してください。')
                else:
                    if target_category not in data['categories']:
                        data['categories'].append(target_category)

                    new_id = max([item.get('id', 0) for item in data['items']] + [0]) + 1
                    
                    sel_title = selected_item['title']
                    sel_type = selected_item.get('type', '映画')
                    sel_orig = selected_item.get('original_title', '')
                    
                    new_entry = {
                        'id': new_id,
                        'title': sel_title,
                        'original_title': sel_orig,
                        'type': sel_type,
                        'category': target_category,
                        'hashtags': final_tags,
                        'memo': memo_input,
                        'year': ''
                    }
                    
                    data['items'].append(new_entry)
                    save_data(data)
                    st.success(f'「{sel_title}」を【{target_category}】カテゴリに登録しました！')
                    st.rerun()

    st.markdown('---')

    # --- タブ表示 ＆ 横断表示 ---
    if selected_tag != 'すべてのアイテム':
        tag_clean = selected_tag.replace('#', '')
        st.subheader(f'🏷️ ハッシュタグ: #{tag_clean} のカテゴリ横断一覧')
        filtered_items = [i for i in data['items'] if tag_clean in i.get('hashtags', [])]
        
        if not filtered_items:
            st.info('このハッシュタグがついたアイテムはありません。')
        else:
            render_item_grid(filtered_items, data)

    else:
        categories = data['categories']
        if categories:
            tabs = st.tabs([f'📁 {cat}' for cat in categories] + ['➕ カテゴリ追加・管理'])
            
            for idx, cat in enumerate(categories):
                with tabs[idx]:
                    cat_items = [i for i in data['items'] if i.get('category') == cat]
                    
                    col_left, col_right = st.columns([3, 1])
                    with col_left:
                        st.subheader(f'「{cat}」のリスト ({len(cat_items)} 件)')
                    with col_right:
                        if len(categories) > 1 and len(cat_items) == 0:
                            if st.button(f'🗑️ このカテゴリ（{cat}）を削除', key=f'del_cat_{cat}'):
                                data['categories'].remove(cat)
                                save_data(data)
                                st.rerun()

                    if not cat_items:
                        st.info('このカテゴリにはまだ登録がありません。上の登録フォームから追加してください。')
                    else:
                        render_item_grid(cat_items, data)

            with tabs[-1]:
                st.subheader('📁 カテゴリの追加・管理')
                new_cat_input = st.text_input('新しいカテゴリ名を入力', key='manage_cat_input')
                if st.button('カテゴリを追加する', key='add_cat_btn'):
                    if new_cat_input.strip() and new_cat_input.strip() not in data['categories']:
                        data['categories'].append(new_cat_input.strip())
                        save_data(data)
                        st.success(f'カテゴリ「{new_cat_input.strip()}」を追加しました！')
                        st.rerun()

if __name__ == '__main__':
    main()
