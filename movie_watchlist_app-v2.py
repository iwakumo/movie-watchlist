import streamlit as st
import json
import os
import urllib.parse
import urllib.request

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

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_online_candidates(query):
    if not query or len(query.strip()) < 1:
        return []
    
    q = query.strip()
    candidates = []
    seen = set()

    # 1. Wikipedia OpenSearch API (人名・監督名・作品名)
    try:
        w_host = 'ja.wiki' + 'pedia.org'
        wiki_url = f'https://{w_host}/w/api.php?action=opensearch&search=' + urllib.parse.quote(q) + '&limit=6&namespace=0&format=json'
        req = urllib.request.Request(wiki_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            titles = res[1] if len(res) > 1 else []
            for t in titles:
                clean_t = t.replace(' (映画)', '').replace(' (監督)', '').strip()
                if clean_t and clean_t not in seen:
                    seen.add(clean_t)
                    ctype = '監督' if '監督' in t else ('映画' if '映画' in t else '人物・作品')
                    candidates.append({
                        'title': clean_t,
                        'original_title': '',
                        'type': ctype,
                        'year': '',
                        'display': f'🔍 {clean_t} （{ctype}の候補）'
                    })
    except Exception:
        pass

    # 2. iTunes Movie Search API (映画タイトル・年・監督)
    try:
        i_host = 'itunes.apple' + '.com'
        itunes_url = f'https://{i_host}/search?term=' + urllib.parse.quote(q) + '&country=jp&media=movie&limit=5'
        req = urllib.request.Request(itunes_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            results = res.get('results', [])
            for r in results:
                track_name = r.get('trackName', '')
                artist_name = r.get('artistName', '')
                release_date = r.get('releaseDate', '')[:4]
                
                if track_name and track_name not in seen:
                    seen.add(track_name)
                    dir_str = f' / 監督: {artist_name}' if artist_name else ''
                    year_str = f' ({release_date})' if release_date else ''
                    candidates.append({
                        'title': track_name,
                        'original_title': '',
                        'type': '映画',
                        'year': release_date,
                        'display': f'🎬 『{track_name}』{year_str}{dir_str}'
                    })
                
                if artist_name and artist_name not in seen:
                    seen.add(artist_name)
                    candidates.append({
                        'title': artist_name,
                        'original_title': '',
                        'type': '監督',
                        'year': '',
                        'display': f'🎥 {artist_name} （映画監督）'
                    })
    except Exception:
        pass

    # フォールバック
    if q not in seen:
        candidates.insert(0, {
            'title': q,
            'original_title': '',
            'type': '映画',
            'year': '',
            'display': f'✍️ 「{q}」（映画としてそのまま登録）'
        })
        candidates.insert(1, {
            'title': q,
            'original_title': '',
            'type': '監督',
            'year': '',
            'display': f'✍️ 「{q}」（監督としてそのまま登録）'
        })

    return candidates

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
                st.markdown(f'**種別:** {item_type} | **カテゴリ:** {item_cat}')
                
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
    with st.expander('➕ 【新しい作品・人物を登録する】 (自動予測候補機能つき)', expanded=True):
        st.markdown('#### ① キーワードを入力する (キーワードの一部から候補を自動推測します)')
        search_kw = st.text_input('作品名や監督名を入力 (例: スコセッシ, ノーラン, オッペンハイマー)', key='kw_input', placeholder='キーワードを入力...')

        if search_kw.strip():
            with st.spinner('予測候補を取得中...'):
                candidates = fetch_online_candidates(search_kw)
            
            st.markdown('#### ② ＆ ③ 予測候補が出てくる ➜ 該当する候補を選択')
            candidate_labels = [c['display'] for c in candidates]
            
            chosen_index = st.radio(
                '一致する候補を選んでください:',
                range(len(candidate_labels)),
                format_func=lambda i: candidate_labels[i],
                key='candidate_radio'
            )
            
            selected_candidate = candidates[chosen_index]
            
            st.markdown('---')
            c_title_col, c_type_col = st.columns([3, 1])
            with c_title_col:
                final_title = st.text_input('登録タイトル（修正可能）:', value=selected_candidate['title'], key='final_title_input')
            with c_type_col:
                type_options = ['映画', '監督', 'キャスト/人物', 'その他']
                default_type_idx = 0
                if selected_candidate['type'] in type_options:
                    default_type_idx = type_options.index(selected_candidate['type'])
                final_type = st.selectbox('種別:', type_options, index=default_type_idx, key='final_type_select')

            col1, col2 = st.columns(2)

            with col1:
                st.markdown('#### ④ 登録先のカテゴリを選ぶ / 作る')
                category_option = st.radio('カテゴリ選択方法:', ['既存のカテゴリから選ぶ', '新しいカテゴリを作成する'], key='cat_opt_radio')
                if category_option == '既存のカテゴリから選ぶ':
                    target_category = st.selectbox('登録先カテゴリ:', data['categories'], key='target_cat_select')
                else:
                    new_cat = st.text_input('新カテゴリ名:', placeholder='例: アカデミー賞2026, アニメ映画', key='new_cat_input')
                    target_category = new_cat.strip()

            with col2:
                st.markdown('#### ⑤ 関連するハッシュタグをつける')
                st.caption('複数指定可（スペースやカンマ区切り）')
                existing_tags_selected = st.multiselect('既存のタグから選択:', all_hashtags, key='multi_tag_select')
                new_tags_input = st.text_input('新しいタグを追加 (例: #サスペンス #A24):', placeholder='#SF #映画館で観たい', key='new_tags_text')
                
                extra_tags = [t.strip('# ').strip() for t in new_tags_input.replace('　', ' ').replace(',', ' ').split(' ') if t.strip()]
                final_tags = sorted(list(set(existing_tags_selected + extra_tags)))

            st.markdown('#### ⑥ 一言メモを入力して ➜ 登録！')
            memo_input = st.text_area('一言メモ (気になっている理由や補足など)', placeholder='例: 映画館の大スクリーンで観たい！', key='memo_area')

            if st.button('🚀 ウォッチリストに登録！', type='primary', key='reg_btn'):
                if not target_category:
                    st.error('登録先カテゴリを指定してください。')
                elif not final_title.strip():
                    st.error('タイトルを入力してください。')
                else:
                    if target_category not in data['categories']:
                        data['categories'].append(target_category)

                    new_id = max([item.get('id', 0) for item in data['items']] + [0]) + 1
                    
                    new_entry = {
                        'id': new_id,
                        'title': final_title.strip(),
                        'original_title': selected_candidate.get('original_title', ''),
                        'type': final_type,
                        'category': target_category,
                        'hashtags': final_tags,
                        'memo': memo_input,
                        'year': selected_candidate.get('year', '')
                    }
                    
                    data['items'].append(new_entry)
                    save_data(data)
                    st.success(f'「{final_title.strip()}」を【{target_category}】カテゴリに登録しました！')
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
