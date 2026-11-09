import streamlit as st
import pandas as pd
import random
import itertools
import os

# 페이지 기본 설정
st.set_page_config(page_title="스마트 로또 번호 추천 프로그램", page_icon="🎰", layout="wide")
st.title("🎰 데이터 영구 저장 및 스마트 로또 추천 프로그램")
st.write("입력한 당첨 데이터가 파일에 영구 저장되며, 잘못 입력한 경우 수정 및 삭제가 가능합니다.")

# 데이터 파일 경로 설정
DB_FILE = "lotto_database.csv"

# 상수 정의
PRIMES = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43} # 소수
CORNER_NUMS = {1, 2, 8, 9, 6, 7, 13, 14, 29, 30, 36, 37, 34, 35, 41, 42} # 모서리 패턴 수
PALINDROMES = {14, 24, 34, 41, 42, 43} # 회문수
PAIRS = {11, 22, 33, 44} # 쌍수

# AC값 계산 함수
def calculate_ac(combo):
    diffs = set()
    for a, b in itertools.combinations(combo, 2):
        diffs.add(abs(a - b))
    return len(diffs) - 5

# 연속 횟수 계산 함수
def calculate_consecutive_count(combo):
    count = 0
    for i in range(len(combo) - 1):
        if combo[i+1] == combo[i] + 1:
            count += 1
    return count

# 조건 검증 함수 (역대 당첨 조합 포함 검증)
def validate_combination(combo, past_info):
    combo_sorted = sorted(combo)
    combo_tuple = tuple(combo_sorted)
    
    past_combinations = past_info.get('past_combinations', set())
    if combo_tuple in past_combinations:
        return False
    
    if not (81 <= sum(combo_sorted) <= 200):
        return False
    if not (13 <= sum(n % 10 for n in combo_sorted) <= 38):
        return False
    if sum(1 for n in combo_sorted if n % 3 == 0) > 4:
        return False
    if sum(1 for n in combo_sorted if n % 5 == 0) > 3:
        return False
    if sum(1 for n in combo_sorted if n in PRIMES) > 3:
        return False
    if calculate_consecutive_count(combo_sorted) > 2:
        return False
        
    odd_count = sum(1 for n in combo_sorted if n % 2 != 0)
    if odd_count == 0 or odd_count == 6:
        return False
        
    high_count = sum(1 for n in combo_sorted if n >= 23)
    if high_count == 0 or high_count == 6:
        return False
        
    if sum(1 for n in combo_sorted if n in PALINDROMES) > 3:
        return False
    if sum(1 for n in combo_sorted if n in PAIRS) > 2:
        return False
    if sum(1 for n in combo_sorted if n > 1 and (n not in PRIMES)) > 4:
        return False
        
    end_digits = [n % 10 for n in combo_sorted]
    if max(end_digits.count(d) for d in set(end_digits)) > 3:
        return False
        
    zones = [0] * 5 
    for n in combo_sorted:
        if n <= 9: zones[0] += 1
        elif n <= 19: zones[1] += 1
        elif n <= 29: zones[2] += 1
        elif n <= 39: zones[3] += 1
        else: zones[4] += 1
    if max(zones) > 3:
        return False
        
    if calculate_ac(combo_sorted) < 6:
        return False
        
    corner_count = sum(1 for n in combo_sorted if n in CORNER_NUMS)
    if not (1 <= corner_count <= 4):
        return False

    if past_info:
        if past_info.get('last_bonus') in combo_sorted:
            return False
        if any(combo_sorted.count(n) for n in combo_sorted if n in past_info.get('frequent_4', set())):
            return False
        if any(combo_sorted.count(n) for n in combo_sorted if n in past_info.get('frequent_10', set())):
            return False
            
        last_nums = past_info.get('last_numbers', set())
        carry_over_count = sum(1 for n in combo_sorted if n in last_nums)
        if not (1 <= carry_over_count <= 2):
            return False
            
        hot_nums = past_info.get('hot_nums', set())
        cold_nums = past_info.get('cold_nums', set())
        
        hot_count = sum(1 for n in combo_sorted if n in hot_nums)
        cold_count = sum(1 for n in combo_sorted if n in cold_nums)
        
        if not (1 <= hot_count <= 2):
            return False
        if not (1 <= cold_count <= 2):
            return False
            
    return True

# --- 데이터 로드 및 저장 함수 ---
def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            return df
        except:
            pass
    # 파일이 없거나 읽기 실패 시 기본 샘플 데이터 반환
    initial_data = [
        {"회차": 1248, "n1": 16, "n2": 18, "n3": 27, "n4": 36, "n5": 38, "n6": 42, "bonus": 22},
        {"회차": 1247, "n1": 8, "n2": 14, "n3": 21, "n4": 22, "n5": 42, "n6": 45, "bonus": 24},
        {"회차": 1246, "n1": 16, "n2": 22, "n3": 23, "n4": 24, "n5": 27, "n6": 28, "bonus": 6},
        {"회차": 1245, "n1": 4, "n2": 5, "n3": 25, "n4": 28, "n5": 32, "n6": 42, "bonus": 12},
        {"회차": 1244, "n1": 1, "n2": 13, "n3": 18, "n4": 26, "n5": 34, "n6": 38, "bonus": 25},
    ]
    df = pd.DataFrame(initial_data)
    df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')
    return df

def save_data(df):
    df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')

# 세션 상태에 데이터 로드
if 'df_lotto' not in st.session_state:
    st.session_state.df_lotto = load_data()

# 사이드바 설정: 새 회차 추가
st.sidebar.header("➕ 새로운 당첨 회차 추가")
with st.sidebar.form("new_draw_form"):
    max_round = int(st.session_state.df_lotto['회차'].max()) if not st.session_state.df_lotto.empty else 1200
    new_round = st.number_input("회차 번호", min_value=1, value=max_round + 1)
    
    st.write("당첨 번호 6개 (1~45)")
    col_a, col_b, col_c, col_d, col_e, col_f = st.columns(6)
    n1 = col_a.number_input("n1", 1, 45, 1)
    n2 = col_b.number_input("n2", 1, 45, 2)
    n3 = col_c.number_input("n3", 1, 45, 3)
    n4 = col_d.number_input("n4", 1, 45, 4)
    n5 = col_e.number_input("n5", 1, 45, 5)
    n6 = col_f.number_input("n6", 1, 45, 6)
    
    new_bonus = st.number_input("보너스 번호", min_value=1, max_value=45, value=7)
    
    submit_button = st.form_submit_button(label="💾 데이터에 추가하기")
    
    if submit_button:
        entered_nums = sorted([n1, n2, n3, n4, n5, n6])
        if len(set(entered_nums)) < 6:
            st.sidebar.error("⚠️ 당첨 번호 6개는 서로 중복될 수 없습니다!")
        elif new_round in st.session_state.df_lotto['회차'].values:
            st.sidebar.error(f"⚠️ 이미 존재하는 {new_round}회차입니다. 아래 수정 기능을 이용해 주세요.")
        else:
            new_row = pd.DataFrame([{
                "회차": new_round, "n1": entered_nums[0], "n2": entered_nums[1], 
                "n3": entered_nums[2], "n4": entered_nums[3], "n5": entered_nums[4], 
                "n6": entered_nums[5], "bonus": new_bonus
            }])
            st.session_state.df_lotto = pd.concat([new_row, st.session_state.df_lotto], ignore_index=True)
            # 회차 기준으로 내림차순 정렬 및 저장
            st.session_state.df_lotto = st.session_state.df_lotto.sort_values(by="회차", ascending=False).reset_index(drop=True)
            save_data(st.session_state.df_lotto)
            st.sidebar.success(f"🎉 {new_round}회차 데이터가 영구 저장되었습니다!")
            st.rerun()

# 사이드바 설정: 잘못 입력한 회차 수정/삭제 기능
st.sidebar.divider()
st.sidebar.subheader("✏️ 데이터 수정 및 삭제")
with st.sidebar.form("edit_delete_form"):
    existing_rounds = sorted(st.session_state.df_lotto['회차'].tolist(), reverse=True)
    selected_round = st.selectbox("관리할 회차 선택", existing_rounds)
    
    # 선택한 회차의 기존 데이터 불러오기
    row_data = st.session_state.df_lotto[st.session_state.df_lotto['회차'] == selected_round].iloc[0]
    
    e_n1 = st.number_input("n1 수정", 1, 45, int(row_data['n1']))
    e_n2 = st.number_input("n2 수정", 1, 45, int(row_data['n2']))
    e_n3 = st.number_input("n3 수정", 1, 45, int(row_data['n3']))
    e_n4 = st.number_input("n4 수정", 1, 45, int(row_data['n4']))
    e_n5 = st.number_input("n5 수정", 1, 45, int(row_data['n5']))
    e_n6 = st.number_input("n6 수정", 1, 45, int(row_data['n6']))
    e_bonus = st.number_input("보너스 수정", 1, 45, int(row_data['bonus']))
    
    col_btn1, col_btn2 = st.columns(2)
    update_btn = col_btn1.form_submit_button("🔄 수정 반영")
    delete_btn = col_btn2.form_submit_button("❌ 회차 삭제")
    
    if update_btn:
        e_nums = sorted([e_n1, e_n2, e_n3, e_n4, e_n5, e_n6])
        if len(set(e_nums)) < 6:
            st.sidebar.error("⚠️ 번호는 중복될 수 없습니다!")
        else:
            idx = st.session_state.df_lotto[st.session_state.df_lotto['회차'] == selected_round].index[0]
            st.session_state.df_lotto.loc[idx, ['n1', 'n2', 'n3', 'n4', 'n5', 'n6', 'bonus']] = [e_nums[0], e_nums[1], e_nums[2], e_nums[3], e_nums[4], e_nums[5], e_bonus]
            save_data(st.session_state.df_lotto)
            st.sidebar.success(f"✅ {selected_round}회차 정보가 수정되었습니다!")
            st.rerun()
            
    if delete_btn:
        st.session_state.df_lotto = st.session_state.df_lotto[st.session_state.df_lotto['회차'] != selected_round].reset_index(drop=True)
        save_data(st.session_state.df_lotto)
        st.sidebar.success(f"🗑️ {selected_round}회차 데이터가 삭제되었습니다!")
        st.rerun()

st.sidebar.divider()
st.sidebar.subheader("🍀 나의 행운의 번호 설정 (선택사항)")
lucky_input = st.sidebar.text_input("최대 12개 입력 가능 (쉼표로 구분)", "")

# --- 데이터 분석 및 통계 처리 ---
past_info = {}
system_excluded_details = []
hot_nums = set()
cold_nums = set()

try:
    df = st.session_state.df_lotto.sort_values(by="회차", ascending=False).reset_index(drop=True)
    
    if set(['n1', 'n2', 'n3', 'n4', 'n5', 'n6']).issubset(df.columns):
        past_combinations = set()
        for _, row in df.iterrows():
            row_nums = tuple(sorted([row['n1'], row['n2'], row['n3'], row['n4'], row['n5'], row['n6']]))
            past_combinations.add(row_nums)
        past_info['past_combinations'] = past_combinations
        
        last_row = df.iloc[0]
        last_numbers = set(last_row[['n1', 'n2', 'n3', 'n4', 'n5', 'n6']].values)
        past_info['last_numbers'] = last_numbers
        
        if 'bonus' in df.columns:
            last_bonus = int(last_row['bonus'])
            past_info['last_bonus'] = last_bonus
            system_excluded_details.append((last_bonus, f"전회차({int(last_row['회차'])}회) 보너스 번호 (이번 회차 조합에서 무조건 제외됨)"))
            
        recent_4 = df.iloc[:4][['n1', 'n2', 'n3', 'n4', 'n5', 'n6']].values.flatten()
        recent_10 = df.iloc[:10][['n1', 'n2', 'n3', 'n4', 'n5', 'n6']].values.flatten()
        
        counts_4 = pd.Series(recent_4).value_counts()
        counts_10 = pd.Series(recent_10).value_counts()
        
        frequent_4 = set(counts_4[counts_4 >= 2].index)
        frequent_10 = set(counts_10[counts_10 >= 4].index)
        
        past_info['frequent_4'] = frequent_4
        past_info['frequent_10'] = frequent_10
        
        for n in sorted(frequent_4):
            if not any(item[0] == n for item in system_excluded_details):
                system_excluded_details.append((n, "직전 4회차 이내 2번 이상 출현하여 과다출현 번호로 제외됨"))
        for n in sorted(frequent_10):
            if not any(item[0] == n for item in system_excluded_details):
                system_excluded_details.append((n, "직전 10회차 이내 4번 이상 출현하여 과다출현 번호로 제외됨"))
        
        recent_5_df = df.iloc[:5][['n1', 'n2', 'n3', 'n4', 'n5', 'n6']]
        hot_nums = set(recent_5_df.values.flatten())
        
        recent_10_all = set(recent_10)
        cold_nums = set(range(1, 46)) - recent_10_all
        
        past_info['hot_nums'] = hot_nums
        past_info['cold_nums'] = cold_nums
        
except Exception as e:
    st.error(f"데이터 처리 오류: {e}")

# 메인 화면 설정
num_games = st.slider("🎲 추천받을 게임 수 선택", min_value=1, max_value=10, value=5)

if st.button("🚀 로또 번호 추출하기"):
    raw_lucky_numbers = []
    if lucky_input.strip():
        try:
            raw_lucky_numbers = [int(x.strip()) for x in lucky_input.split(",") if x.strip().isdigit()]
            raw_lucky_numbers = [n for n in raw_lucky_numbers if 1 <= n <= 45][:12]
        except:
            pass

    user_excluded_details = []
    available_lucky = []
    
    if raw_lucky_numbers:
        for n in raw_lucky_numbers:
            reasons = []
            if past_info:
                if n == past_info.get('last_bonus'):
                    reasons.append("전회차 보너스 번호에 해당")
                if n in past_info.get('frequent_4', set()):
                    reasons.append("직전 4회차 이내 2번 이상 출현한 과다출현 번호")
                if n in past_info.get('frequent_10', set()):
                    reasons.append("직전 10회차 이내 4번 이상 출현한 과다출현 번호")
                    
            if reasons:
                user_excluded_details.append((n, ", ".join(reasons)))
            else:
                available_lucky.append(n)

    recommended_combos = []
    attempts = 0
    max_attempts = 500000
    
    while len(recommended_combos) < num_games and attempts < max_attempts:
        attempts += 1
        combo_candidate = set()
        
        if hot_nums:
            h_count = random.randint(1, 2)
            sampled_hot = random.sample(list(hot_nums), min(h_count, len(hot_nums)))
            combo_candidate.update(sampled_hot)
            
        if cold_nums:
            c_count = random.randint(1, 2)
            sampled_cold = random.sample(list(cold_nums), min(c_count, len(cold_nums)))
            combo_candidate.update(sampled_cold)
            
        if available_lucky and random.random() < 0.5:
            sample_count = min(len(available_lucky), random.randint(1, 2))
            combo_candidate.update(random.sample(available_lucky, sample_count))
            
        remaining_pool = [n for n in range(1, 46) if n not in combo_candidate]
        needed_count = 6 - len(combo_candidate)
        
        if len(remaining_pool) >= needed_count and needed_count >= 0:
            combo_candidate.update(random.sample(remaining_pool, needed_count))
            combo = sorted(list(combo_candidate))
            
            if len(combo) == 6 and validate_combination(combo, past_info):
                if combo not in recommended_combos:
                    recommended_combos.append(combo)

    if len(recommended_combos) < num_games:
        st.warning(f"⚠️ 조건이 너무 엄격하여 {num_games}개 중 {len(recommended_combos)}개만 생성되었습니다. (다시 시도하면 더 많이 생성될 수 있습니다)")

    st.divider()
    
    if hot_nums and cold_nums:
        st.subheader("🔥 핫수 및 ❄️ 콜드수 분석 현황")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**🔥 핫수 (최근 5회 이내 출현, 총 {len(hot_nums)}개)**")
            st.write(sorted(list(hot_nums)))
        with col2:
            st.markdown(f"**❄️ 콜드수 (최근 10주 미출현, 총 {len(cold_nums)}개)**")
            st.write(sorted(list(cold_nums)))
        st.divider()

    st.subheader("🛡️ 프로그램 자동 제외 번호 및 사유 안내")
    if system_excluded_details:
        st.info("💡 본 프로그램의 통계 및 과거 데이터 기준에 따라 **이번 회차 조합에서 자동 제외된 번호 목록**입니다.")
        for num, reason in sorted(system_excluded_details, key=lambda x: x[0]):
            st.markdown(f"- **{num}번**: {reason}")
        if 'past_combinations' in past_info:
            st.markdown(f"- **역대 당첨 조합 필터**: 총 {len(past_info['past_combinations'])}회의 역대 당첨 번호 조합과 **동일한 6개 번호 세트**는 추천에서 원천 제외되었습니다.")

    if raw_lucky_numbers:
        st.markdown("---")
        st.markdown(f"**🍀 입력하신 행운의 번호:** `{sorted(raw_lucky_numbers)}`")
        if user_excluded_details:
            st.warning("⚠️ **[행운의 번호 중 필터링된 내역]**")
            for num, reason in user_excluded_details:
                st.markdown(f"- **{num}번**: {reason} 때문에 행운의 번호 목록에서 제외되었습니다.")
        else:
            st.success("✨ 입력하신 행운의 번호 중 프로그램 필터에 걸리는 번호가 없어 모두 유효하게 반영되었습니다!")

    st.divider()
    st.subheader("🎉 조건 충족 추천 로또 번호")
    for i, combo in enumerate(recommended_combos, 1):
        h_in = sum(1 for n in combo if n in hot_nums)
        c_in = sum(1 for n in combo if n in cold_nums)
        
        formatted_combo = "  |  ".join(f"**{n:02d}**" for n in combo)
        st.markdown(f"**{i}게임:** {formatted_combo} &nbsp;&nbsp;&nbsp; <span style='color:gray; font-size:0.9em;'>(핫수 {h_in}개, 콜드수 {c_in}개)</span>", unsafe_allow_html=True)

# 하단에 현재 영구 저장된 데이터 목록 확인 아코디언 제공
with st.expander("📋 현재 저장된 역대 당첨 데이터 확인하기 (클릭하여 열기)"):
    st.dataframe(st.session_state.df_lotto, use_container_width=True)