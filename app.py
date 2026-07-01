import streamlit as st
import json
import os
from supabase import create_client
from dotenv import load_dotenv
import streamlit as st

# 1. إعداد كلمة السر
PASSWORD = "123"  # بدل 123 بالكود اللي بغيتي

# 2. شاشة الدخول
password_input = st.text_input("ادخل كلمة السر للدخول:", type="password")

if password_input == PASSWORD:
    st.success("مرحبا بك في تطبيق العيادة!")
    # هنا حط باقي الكود ديال التطبيق ديالك كامل
    # مثلاً:
    # st.write("هنا داتا ديال المرضى...")
else:
    st.warning("المرجو إدخال كلمة السر للدخول.")
    st.stop() # هاد السطر كيوقف التطبيق وما كيخلي حتى شي حاجة تبان من التحت

# --- 1. الاتصال بـ السحاب ---
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
BUCKET_NAME = "dental_bucket"

def save_json(filename, data):
    try:
        bytes_data = json.dumps(data, ensure_ascii=False, indent=4).encode('utf-8')
        supabase.storage.from_(BUCKET_NAME).upload(
            path=filename,
            file=bytes_data,
            file_options={"cache-control": "3600", "upsert": "true"}
        )
        return True
    except Exception as e:
        st.error(f"❌ مشكل فـ تحديث السحاب: {e}")
        return False

def fetch_json(filename):
    try:
        res = supabase.storage.from_(BUCKET_NAME).download(filename)
        return json.loads(res.decode('utf-8'))
    except:
        return []

# --- 2. إعدادات الصفحة والذاكرة ---
st.set_page_config(page_title="Dental Dashboard", layout="wide")

if 'section_ouverte' not in st.session_state:
    st.session_state.section_ouverte = None

def ouvrir_section(nom_section):
    st.session_state.section_ouverte = nom_section

# --- 3. دالة حساب الديون والفائض ---
def calculer_balance_totale():
    m_data = fetch_json("materiel.json")
    p_data = fetch_json("produits.json")
    b_data = fetch_json("bons.json")
    
    def get_dette_et_faid(item, type_data):
        reste = float(item.get('reste', 0))
        if 'reste' not in item:
            total = float(item.get('prix_total', item.get('prix', item.get('total', 0))))
            hist = item.get('historique_paiements', item.get('paiements', []))
            verse = sum(float(p.get('montant', 0)) for p in hist)
            reste = total - verse
        return reste

    bal_m = sum(get_dette_et_faid(m, 'materiel') for m in m_data)
    bal_p = sum(get_dette_et_faid(p, 'produits') for p in p_data)
    bal_b = sum(get_dette_et_faid(b, 'bons') for b in b_data)
    total_net = bal_m + bal_p + bal_b
    return total_net, bal_b, bal_p, bal_m

total_balance, balance_bons, balance_produits, balance_materiel = calculer_balance_totale()
faid = sum(abs(x) for x in [balance_bons, balance_produits, balance_materiel] if x < 0)

def format_balance(val):
    if val > 0: return f"{val:.2f} DH"
    elif val < 0: return f"فائض: {abs(val):.2f} DH"
    else: return "0.00 DH"

# ====================================================
# 💰 القسم العلوي: المربعات
# ====================================================
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.button(f"🔴 الصافي العام\n{format_balance(total_balance)}", use_container_width=True)
with col2:
    st.button(f"🧾 بونات\n{format_balance(balance_bons)}", on_click=ouvrir_section, args=('bons',), use_container_width=True)
with col3:
    st.button(f"📦 المنتجات\n{format_balance(balance_produits)}", on_click=ouvrir_section, args=('produits',), use_container_width=True)
with col4:
    st.button(f"🛠️ الماتريال\n{format_balance(balance_materiel)}", on_click=ouvrir_section, args=('materiel',), use_container_width=True)
with col1:
    st.metric("🟢 إجمالي الفائض (ليك)", f"{faid:.2f} DH")

st.markdown("### 🗂️ ملفات العيادة")

# ====================================================
# 👥 1. مستطيل المرضى
# ====================================================
with st.expander("👥 المرضى (Patients)", expanded=(st.session_state.section_ouverte == 'patients')):
    patients_data = fetch_json("patients.json")
    
    if not patients_data:
        st.warning("⚠️ لم يتم العثور على أي بيانات للمرضى فـ السحاب.")
    else:
        col_normal, col_urgent = st.columns(2)
        
        # 🟢 العمود الأول: المرضى العاديين
        with col_normal:
            st.markdown("#### 🟢 المرضى العاديين (Normales)")
            st.markdown("---")
            
            for idx, p in enumerate(patients_data):
                p_urgent = p.get('urgent') or p.get('Urgent') or False
                if not p_urgent:
                    # مReference فريد للمسح
                    p_id = p.get('id') or f"{p.get('nom')}_{idx}"
                    p_name = p.get('Nom') or p.get('nom') or 'مريض بدون اسم'
                    p_phone = p.get('Phone') or p.get('phone') or p.get('tele') or p.get('Tele') or '---'
                    p_traitement = p.get('Traitement') or p.get('traitement') or '---'
                    p_date = p.get('Date') or p.get('date') or '---'
                    p_prix = p.get('Prix') or p.get('prix') or 0
                    
                    with st.expander(f"👤 {p_name} | 🗓️ {p_date}"):
                        c1, c2, c3 = st.columns([2, 1, 1])
                        with c1: st.subheader("🧾 تفاصيل الملف")
                        with c2:
                            # 1. تجميع البيانات للحساب
                            p_prix_val = float(p.get('prix') or p.get('Prix') or 0)
                            p_installments = p.get('paiements') or p.get('Paiements') or p.get('installments') or []
                            
                            # حساب المجموع والمدفوع بدقة للبون
                            total_paid_bon = 0.0
                            payment_details_text = ""
                            if p_installments and isinstance(p_installments, list):
                                for i, inst in enumerate(p_installments):
                                    amount = float(inst.get('amount') or inst.get('montant') or inst.get('prix', 0)) if isinstance(inst, dict) else float(inst)
                                    date_p = inst.get('date', '---') if isinstance(inst, dict) else '---'
                                    payment_details_text += f"الدفعة {i+1}: {amount} DH | بتاريخ: {date_p}\n"
                                    total_paid_bon += amount
                            else:
                                payment_details_text = "لا توجد دفعات مسجلة.\n"
                            
                            p_reste_bon = p_prix_val - total_paid_bon

                            # 2. بناء نص البون الشامل (نفس التنسيق المفضل لديك)
                            bon_text_pat = f"========================================\n"
                            bon_text_pat += f"          👤 وصل ملف مريض (عادي)\n"
                            bon_text_pat += f"========================================\n"
                            bon_text_pat += f"الاسم الكامل: {p_name}\n"
                            bon_text_pat += f"رقم الهاتف: {p_phone}\n"
                            
                            bon_text_pat += f"تاريخ التسجيل: {p_date}\n"
                            bon_text_pat += f"----------------------------------------\n"
                            bon_text_pat += f"الثمن الإجمالي: {p_prix_val:.2f} DH\n"
                            bon_text_pat += f"مجموع المدفوع: {total_paid_bon:.2f} DH\n"
                            bon_text_pat += f"الباقي (Reste): {p_reste_bon:.2f} DH\n"
                            bon_text_pat += f"----------------------------------------\n"
                            bon_text_pat += f"          💳 سجل الدفعات التفصيلي:\n"
                            bon_text_pat += payment_details_text
                            bon_text_pat += f"========================================\n"
                            bon_text_pat += f"شكراً لثقتكم.\n"

                            # 3. زر التحميل بترميز utf-8-sig للقراءة في الهاتف
                            st.download_button(
                                label="📥 حفظ البون", 
                                data=bon_text_pat.encode('utf-8-sig'), 
                                file_name=f"Patient_{p_name}.txt", 
                                mime="text/plain; charset=utf-8",
                                key=f"dl_pat_{p_id}"
                            )
                        with c3:
                            # 🎯 التعديل الفولاذي: المسح بالـ ID أو بالفلترة
                            if st.button("🗑️ مسح", key=f"del_norm_{p_id}"):
                                # فلترة القائمة لإزالة المريض المختار فقط
                                updated_patients = [item for item in patients_data if (item.get('id') != p.get('id') if p.get('id') else item != p)]
                                if save_json("patients.json", updated_patients):
                                    st.success("🗑️ تم المسح!")
                                    st.rerun()

                        st.markdown("<div style='background-color: #ffffff; border: 2px dashed #007bff; padding: 15px; border-radius: 5px; font-family: monospace;'>", unsafe_allow_html=True)
                        st.write(f"**الاسم الكامل:** {p_name}")
                        st.write(f"**الهاتف:** {p_phone}")
                        st.write(f"**نوع العلاج:** {p_traitement}")
                        st.write(f"**التاريخ:** {p_date}")
                        st.write(f"**الثمن الإجمالي:** {p_prix} DH")

                        st.markdown("<hr style='border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)
                        st.markdown("<h4>💳 سجل الدفعات</h4>", unsafe_allow_html=True)
                        
                        p_installments = p.get('paiements') or p.get('Paiements') or p.get('installments') or []
                        total_paid = 0.0
                        if p_installments and isinstance(p_installments, list):
                           for i, inst in enumerate(p_installments):
                               amount = float(inst.get('amount') or inst.get('montant') or inst.get('prix', 0)) if isinstance(inst, dict) else float(inst)
                               date_inst = inst.get('date', '---') if isinstance(inst, dict) else '---'
                               st.caption(f"🔹 الدفعة {i+1}: **{amount} DH** | 🗓️ {date_inst}")
                               total_paid += amount
                           reste = float(p_prix) - total_paid
                           col_p1, col_p2 = st.columns(2)
                           col_p1.metric(" مجموع المدفوع", f"{total_paid:.2f} DH")
                           col_p2.metric(" الباقي (Reste)", f"{reste:.2f} DH", delta=f"-{reste:.2f} DH" if reste > 0 else "خالص", delta_color="inverse")
                        else:
                            st.caption("⚠️ لا توجد دفعات مسجلة.")
                            st.metric(" الباقي (Reste)", f"{p_prix} DH")
                        st.markdown("</div>", unsafe_allow_html=True)

        # 🚨 العمود الثاني: الحالات المستعجلة
        with col_urgent:
            st.markdown("####  الحالات المستعجلة (Urgentes)")
            st.markdown("---")
            urgent_count = 0
            for idx, p in enumerate(patients_data):
                p_urgent = p.get('urgent') or p.get('Urgent') or False
                if p_urgent:
                    urgent_count += 1
                    p_id = p.get('id') or f"urg_{p.get('nom')}_{idx}"
                    p_name = p.get('Nom') or p.get('nom') or 'حالة مستعجلة'
                    p_phone = p.get('Phone') or p.get('phone') or p.get('tele') or p.get('Tele') or '---'
                    p_traitement = p.get('Traitement') or p.get('traitement') or '---'
                    p_date = p.get('Date') or p.get('date') or '---'
                    p_prix = float(p.get('Prix') or p.get('prix') or 0)
                    p_installments = p.get('paiements') or p.get('Paiements') or p.get('installments') or []

                    with st.expander(f" {p_name} |  {p_date}"):
                        c1, c2, c3 = st.columns([2, 1, 1])
                        with c1: st.subheader(" تذكرة عاجلة")
                        with c2:
                            # 1. تجميع البيانات للحساب
                            p_prix_val = float(p.get('prix') or p.get('Prix') or 0)
                            p_installments = p.get('paiements') or p.get('Paiements') or p.get('installments') or []
                            
                            total_paid_bon = 0.0
                            payment_details_text = ""
                            if p_installments and isinstance(p_installments, list):
                                for i, inst in enumerate(p_installments):
                                    amount = float(inst.get('amount') or inst.get('montant') or inst.get('prix', 0)) if isinstance(inst, dict) else float(inst)
                                    date_p = inst.get('date', '---') if isinstance(inst, dict) else '---'
                                    payment_details_text += f"الدفعة {i+1}: {amount} DH | بتاريخ: {date_p}\n"
                                    total_paid_bon += amount
                            else:
                                payment_details_text = "لا توجد دفعات مسجلة.\n"
                            
                            p_reste_bon = p_prix_val - total_paid_bon

                            # 2. بناء نص البون للمستعجل
                            bon_text_urg = f"========================================\n"
                            bon_text_urg += f"          🚨 وصل حالة مستعجلة (Urgent)\n"
                            bon_text_urg += f"========================================\n"
                            bon_text_urg += f"الاسم الكامل: {p_name}\n"
                            bon_text_urg += f"رقم الهاتف: {p_phone}\n"
                            
                            bon_text_urg += f"التاريخ: {p_date}\n"
                            bon_text_urg += f"----------------------------------------\n"
                            bon_text_urg += f"الثمن الإجمالي: {p_prix_val:.2f} DH\n"
                            bon_text_urg += f"مجموع المدفوع: {total_paid_bon:.2f} DH\n"
                            bon_text_urg += f"الباقي (Reste): {p_reste_bon:.2f} DH\n"
                            bon_text_urg += f"----------------------------------------\n"
                            bon_text_urg += f"          💳 سجل الدفعات التفصيلي:\n"
                            bon_text_urg += payment_details_text
                            bon_text_urg += f"========================================\n"

                            st.download_button(
                                label="📥 حفظ البون", 
                                data=bon_text_urg.encode('utf-8-sig'), 
                                file_name=f"Urgent_{p_name}.txt", 
                                mime="text/plain; charset=utf-8",
                                key=f"dl_urg_{p_id}"
                            )
                        with c3:
                            # 🎯 التعديل الفولاذي: المسح بالـ ID
                            if st.button(" مسح", key=f"del_urg_{p_id}"):
                                updated_patients = [item for item in patients_data if (item.get('id') != p.get('id') if p.get('id') else item != p)]
                                if save_json("patients.json", updated_patients):
                                    st.success(" تم مسح الحالة!")
                                    st.rerun()

                        st.markdown("<div style='background-color: #fff5f5; border: 2px dashed #dc3545; padding: 15px; border-radius: 5px; font-family: monospace;'>", unsafe_allow_html=True)
                        st.write(f"**الاسم الكامل:** {p_name}")
                        st.write(f"**الهاتف:** {p_phone}")
                        st.write(f"**العلاج المطلوب:** {p_traitement}")
                        st.write(f"**التاريخ:** {p_date}")
                        st.write(f"**الثمن الإجمالي:** {p_prix} DH")
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        st.markdown("#####  وضعية الدفع والدفعات:")
                        total_paid = 0.0
                        if p_installments and isinstance(p_installments, list):
                            for i, inst in enumerate(p_installments):
                                amount = float(inst.get('amount') or inst.get('montant', 0)) if isinstance(inst, dict) else float(inst)
                                date_inst = inst.get('date', '---') if isinstance(inst, dict) else '---'
                                st.caption(f"🔹 الدفعة {i+1}: **{amount} DH** بتاريخ {date_inst}")
                                total_paid += amount
                            reste = p_prix - total_paid
                            col_p1, col_p2 = st.columns(2)
                            col_p1.metric(" مجموع المدفوع", f"{total_paid} DH")
                            col_p2.metric(" الباقي (Reste)", f"{reste} DH", delta=f"-{reste} DH" if reste > 0 else "خالص", delta_color="inverse")
                        else:
                             st.warning(" لا توجد أي دفعة مسجلة.")
                             st.metric(" الباقي (Reste)", f"{p_prix} DH")
            if urgent_count == 0:
                st.info("🔵 لا توجد أي حالة مستعجلة حالياً.")
# 2. مستطيل المواعيد
with st.expander("📅 المواعيد (RDV)", expanded=(st.session_state.section_ouverte == 'rdv')):
    # 🎯 الربط الصحيح نيشان مع ملف appointments.json ف السحاب
    rdv_data = fetch_json("appointments.json")
    
    if not rdv_data:
        st.info("🔵 لم يتم العثور على أي مواعيد فـ ملف appointments.json فـ السحاب.")
    else:
        import datetime as dt
        
        # --- [تعديل فولاذي]: استخراج المعرفات (IDs) المختارة للمسح بدلاً من الأرقام الترتيبية ---
        selected_ids = [
            k.replace("chk_rdv_", "") 
            for k, v in st.session_state.items() 
            if k.startswith("chk_rdv_") and v
        ]
        
        # إيلا كوشيتي شي حاجة كيبان زر المسح الفوق ديريكت
        if selected_ids:
            st.warning(f"⚠️ لقد قمت بتحديد {len(selected_ids)} مواعيد.")
            if st.button(f"🗑️ مسح المواعيد المحددة ({len(selected_ids)}) نهائياً", type="primary"):
                
                # 🎯 [تعديل فولاذي]: المسح بالفلترة (البحث عن الـ ID) وليس بـ pop(idx)
                # هادي هي الطريقة اللي كتحمي البيانات يلا تبدل الترتيب
                rdv_data = [r for r in rdv_data if str(r.get('id', '')) not in selected_ids]
                
                # 🎯 تحديث نفس الملف الصحيح ف السحاب فاش كتمسح
                if save_json("appointments.json", rdv_data):
                    st.success("🗑️ تم المسح بنجاح!")
                    # تنظيف الذاكرة المؤقتة للـ checkboxes اللي تمسحو
                    for sid in selected_ids:
                        key_to_del = f"chk_rdv_{sid}"
                        if key_to_del in st.session_state:
                            del st.session_state[key_to_del]
                    st.rerun()
            st.markdown("---")
        
        # 🎯 2. فرز المواعيد حسب التاريخ
        aujourdhui_1 = dt.date.today().strftime('%Y-%m-%d')
        aujourdhui_2 = dt.date.today().strftime('%d/%m/%Y')
        
        mide_aujourdhui = []
        mide_autres = {}
        
        for idx, r in enumerate(rdv_data):
            # 🎯 [تعديل فولاذي]: تحديد ID فريد لكل موعد (إما الـ id من السحاب أو صنع واحد مؤقت)
            r_id = str(r.get('id', f"temp_{idx}")) 
            
            r_name = r.get('Nom') or r.get('nom') or 'بدون اسم'
            r_date = r.get('Date') or r.get('date') or '---'
            r_heure = r.get('Heure') or r.get('heure') or r.get('time') or r.get('Time') or '---'
            r_traitement = r.get('traitement') or r.get('Traitement') or '---'
            
            item_info = {'id': r_id, 'nom': r_name, 'date': r_date, 'heure': r_heure, 'traitement': r_traitement}
            
            if r_date == aujourdhui_1 or r_date == aujourdhui_2:
                mide_aujourdhui.append(item_info)
            else:
                if r_date not in mide_autres:
                    mide_autres[r_date] = []
                mide_autres[r_date].append(item_info)
        
        # ====================================================
        # 🟢 مواعيد اليوم (24h الحالية)
        # ====================================================
        st.markdown("#### ⏰ مواعيد الـ 24 ساعة الحالية (اليوم)")
        
        if mide_aujourdhui:
            h_chk, h_nom, h_date, h_heur, h_trait = st.columns([1, 4, 2, 2, 3])
            h_nom.markdown("**👤 الاسم الكامل**")
            h_date.markdown("**🗓️ التاريخ**")
            h_heur.markdown("**🕒 الساعة**")
            h_trait.markdown("**📋 العلاج**")
            st.markdown("<hr style='margin:5px 0;'>", unsafe_allow_html=True)
            
            for item in mide_aujourdhui:
                c_chk, c_nom, c_date, c_heur, c_trait = st.columns([1, 4, 2, 2, 3])
                with c_chk:
                    # 🎯 [تعديل فولاذي]: الـ key مرتبط بـ ID الموعد وليس بـ idx
                    st.checkbox("تحديد", key=f"chk_rdv_{item['id']}", label_visibility="collapsed")
                c_nom.write(item['nom'])
                c_date.write(item['date'])
                c_heur.markdown(f"<span style='color:#28a745; font-weight:bold;'>{item['heure']}</span>", unsafe_allow_html=True)
                c_trait.write(item['traitement'])
        else:
            st.caption("👍 لا توجد مواعيد مجدولة لليوم.")
            
        st.markdown("---")
        
        # ====================================================
        # 📂 أرشيف المواعيد د الأيام الأخرى
        # ====================================================
        st.markdown("#### 🗂️ أرشيف وباقي المواعيد القادمة")
        
        if mide_autres:
            for d_str in sorted(mide_autres.keys(), reverse=True):
                with st.expander(f"🗓️ مواعيد تاريخ: {d_str} 👈 ({len(mide_autres[d_str])} مواعيد)"):
                    h_chk, h_nom, h_date, h_heur, h_trait = st.columns([1, 4, 2, 2, 3])
                    h_nom.markdown("**👤 الاسم**")
                    h_date.markdown("**🗓️ التاريخ**")
                    h_heur.markdown("**🕒 الساعة**")
                    h_trait.markdown("**📋 العلاج**")
                    st.markdown("<hr style='margin:5px 0;'>", unsafe_allow_html=True)
                    
                    for item in mide_autres[d_str]:
                        c_chk, c_nom, c_date, c_heur, c_trait = st.columns([1, 4, 2, 2, 3])
                        with c_chk:
                            # 🎯 [تعديل فولاذي]: الـ key مرتبط بـ ID الموعد
                            st.checkbox("تحديد", key=f"chk_rdv_{item['id']}", label_visibility="collapsed")
                        c_nom.write(item['nom'])
                        c_date.write(item['date'])
                        c_heur.write(item['heure'])
                        c_trait.write(item['traitement'])
        else:
            st.caption("لا توجد أي مواعيد فـ أيام أخرى.")
            
# 1. مستطيل السلع والمعدات (Matériel)
with st.expander("📦 السلع والمعدات (Matériel)", expanded=(st.session_state.get('section_ouverte') == 'materiel')):
    materiel_data = fetch_json("materiel.json")
    
    if not materiel_data:
        st.warning("⚠️ لم يتم العثور على أي بيانات للسلع فـ السحاب (materiel.json).")
    else:
        st.markdown("#### 📦 قائمة السلع، المشتريات والدفعات")
        st.markdown("---")
        
        for idx, m in enumerate(materiel_data):
            # 🎯 [تعديل فولاذي]: تحديد ID فريد للمنتج لضمان دقة المسح والتحميل
            m_id = m.get('id') or f"{m.get('nom')}_{idx}"
            
            m_article = m.get('nom', 'منتوج بدون اسم')
            m_quantite = m.get('quantite', '---')
            m_vendeur = m.get('vendeur', '---')
            m_date = m.get('date', '---')
            
            try:
                m_prix = float(m.get('prix_total', 0.0))
            except:
                m_prix = 0.0

            m_versements = m.get('historique_paiements', [])

            with st.expander(f"📦 {m_article} (الكمية: {m_quantite}) | 🏪 المورد: {m_vendeur}"):
                
                c1, c2, c3 = st.columns([2, 1, 1])
                with c1:
                    st.subheader("🧾 تفاصيل المنتوج")
                with c2:
                    hist_mat = m.get('historique_paiements', [])
                    m_prix_val = float(m.get('prix_total') or m.get('prix') or 0)
                    m_verse = sum(float(pay.get('montant', 0)) for pay in hist_mat)
                    m_reste = m_prix_val - m_verse

                    bon_text_mat = "========================================\n"
                    bon_text_mat += "          🧾 تفاصيل المعدات / السلع\n"
                    bon_text_mat += "========================================\n"
                    bon_text_mat += f"المنتوج: {m.get('nom', '---')}\n"
                    bon_text_mat += f"الكمية: {m.get('quantite', '---')}\n"
                    bon_text_mat += f"المورد: {m.get('vendeur', '---')}\n"
                    bon_text_mat += f"تاريخ الشراء: {m.get('date', '---')}\n"
                    bon_text_mat += "----------------------------------------\n"
                    bon_text_mat += f"الثمن الإجمالي: {m_prix_val:.2f} DH\n"
                    bon_text_mat += f"مجموع المدفوع: {m_verse:.2f} DH\n"
                    bon_text_mat += f"الباقي (Reste): {m_reste:.2f} DH\n"
                    bon_text_mat += "========================================\n"
                    bon_text_mat += "          💳 سجل الدفعات\n"
                    bon_text_mat += "----------------------------------------\n"

                    if hist_mat:
                        for i, pay in enumerate(hist_mat):
                            bon_text_mat += f"الدفعة {i+1}: {pay.get('montant', 0)} DH (بتاريخ: {pay.get('date', '---')})\n"
                    else:
                        bon_text_mat += "لا توجد أي دفعة مسجلة حالياً.\n"
                    bon_text_mat += "========================================\n"

                    st.download_button(
                        label="📥 حفظ الماتيريال", 
                        data=bon_text_mat.encode('utf-8-sig'), 
                        file_name=f"Bon_Materiel_{m_article}.txt", 
                        mime="text/plain; charset=utf-8", 
                        key=f"dl_mat_{m_id}" # 🎯 [تعديل فولاذي]: Key فريد بالـ ID
                     )
                with c3:
                    # 🎯 [تعديل فولاذي]: المسح بالـ ID والفلترة لضمان عدم حذف عنصر خاطئ
                    if st.button("🗑️ مسح", key=f"del_mat_{m_id}", help="مسح نهائي من السحاب"):
                        # الفلترة: نحتفظ بكل شيء ما عدا هذا الـ ID
                        new_materiel_data = [item for item in materiel_data if (item.get('id') != m.get('id') if m.get('id') else item != m)]
                        if save_json("materiel.json", new_materiel_data): 
                            st.success("🗑️ تم المسح بنجاح!")
                            st.rerun() 

                st.markdown("<div style='background-color: #f8f9fa; border: 2px dashed #17a2b8; padding: 15px; border-radius: 5px; font-family: monospace;'>", unsafe_allow_html=True)
                st.write(f"**المنتوج (Article):** {m_article}")
                st.write(f"**الكمية (Quantité):** {m_quantite}")
                st.write(f"**المورد (Vendeur/Frs):** {m_vendeur}")
                st.write(f"**تاريخ الشراء (Date Achat):** {m_date}")
                st.write(f"**الثمن الإجمالي (Prix Total):** {m_prix} DH")
                st.markdown("</div>", unsafe_allow_html=True)
                
                st.markdown("<hr style='border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)
                st.markdown("##### 💳 وضعية الدفع والدفعات:")

                total_paid = 0.0
                if m_versements and isinstance(m_versements, list):
                    for i, inst in enumerate(m_versements):
                        if isinstance(inst, dict):
                            amount = float(inst.get('montant', 0))
                            date_inst = inst.get('date', '---')
                            st.caption(f"🔹 الدفعة {i+1}: **{amount} DH** بتاريخ {date_inst}")
                            total_paid += amount
                        else:
                            try:
                                amount = float(inst)
                                st.caption(f"🔹 الدفعة {i+1}: **{amount} DH**")
                                total_paid += amount
                            except: pass
                else:
                    st.caption("⚠️ لا توجد أي دفعة مسجلة حالياً.")

                reste = m_prix - total_paid
                col_p1, col_p2 = st.columns(2)
                col_p1.metric("💰 مجموع المدفوع", f"{total_paid} DH")
                
                if reste > 0:
                    col_p2.metric("🔴 الباقي (Reste)", f"{reste} DH", delta=f"-{reste} DH", delta_color="inverse")
                elif reste < 0:
                    col_p2.metric("🟡 الباقي (Reste)", f"0 DH (فائض: {abs(reste)} DH)")
                else:
                    col_p2.metric("🟢 الباقي (Reste)", "0 DH", delta="Payé / خالص", delta_color="normal")
# 4. مستطيل المنتوجات والبونات
# --- واجهة إدارة المنتجات والوصولات ---
st.header("📦 إدارة المخزون والمبيعات")

# 2. مستطيل المنتجات (Produits)
with st.expander("🛍️ المنتجات (Produits)", expanded=(st.session_state.get('section_ouverte') == 'produits')):
    prod_data = fetch_json("produits.json")
    if not prod_data:
        st.info("🔵 لا توجد منتجات مسجلة حالياً.")
    else:
        for idx, p in enumerate(prod_data):
            # 🎯 [تعديل فولاذي]: تحديد ID فريد للمنتج
            p_id = p.get('id') or f"prod_{p.get('nom')}_{idx}"
            
            p_name = p.get('nom', 'منتج بدون اسم')
            p_prix = float(p.get('prix', 0))
            p_verse = float(p.get('verse', 0))
            p_reste = float(p.get('reste', 0))
            p_type = p.get('type', '---')
            p_date = p.get('date', '---')

            with st.expander(f"🛍️ {p_name} | المتبقي: {p_reste} DH"):
                
                # --- العنوان والبوطونات ---
                c1, c2, c3 = st.columns([2, 1, 1])
                with c1:
                    st.subheader("🧾 تفاصيل المنتوج")
                with c2:
                    # --- تجهيز نص البون مفصل للمنتجات ---
                    bon_text = f"========================================\n"
                    bon_text += f"          🧾 تفاصيل المنتوج\n"
                    bon_text += f"========================================\n"
                    bon_text += f"المنتوج: {p_name}\n"
                    bon_text += f"النوع: {p_type}\n"
                    bon_text += f"تاريخ التسجيل: {p_date}\n"
                    bon_text += f"----------------------------------------\n"
                    bon_text += f"الثمن الإجمالي: {p_prix} DH\n"
                    bon_text += f"مجموع المدفوع: {p_verse} DH\n"
                    bon_text += f"الباقي (Reste): {p_reste} DH\n"
                    bon_text += f"========================================\n"
                    bon_text += f"          💳 سجل الدفعات\n"
                    bon_text += f"----------------------------------------\n"

                    hist = p.get('historique_paiements', [])
                    if hist:
                        for i, pay in enumerate(hist):
                            bon_text += f"الدفعة {i+1}: {pay.get('montant')} DH (بتاريخ: {pay.get('date')})\n"
                    else:
                        bon_text += "لا توجد أي دفعة مسجلة حالياً.\n"
                    bon_text += f"========================================\n"

                    st.download_button(
                        label="📥 حفظ", 
                        data=bon_text.encode('utf-8-sig'), 
                        file_name=f"Bon_Prod_{p_name}.txt", 
                        mime="text/plain; charset=utf-8", 
                        key=f"dl_prod_{p_id}" # 🎯 [تعديل فولاذي]: Key فريد بالـ ID
                      )
                with c3:
                    # 🎯 [تعديل فولاذي]: المسح بالـ ID لضمان عدم حذف عنصر خاطئ
                    if st.button("🗑️ مسح", key=f"del_prod_{p_id}"):
                        new_prod_data = [item for item in prod_data if (item.get('id') != p.get('id') if p.get('id') else item != p)]
                        if save_json("produits.json", new_prod_data):
                            st.success("🗑️ تم المسح!")
                            st.rerun()

                # --- المربع المنظم ديال المعلومات ---
                st.markdown("<div style='background-color: #f8f9fa; border: 2px dashed #17a2b8; padding: 15px; border-radius: 5px; font-family: monospace; color: #000;'>", unsafe_allow_html=True)
                st.write(f"**المنتوج (Article):** {p_name}")
                st.write(f"**النوع (Type):** {p_type}")
                st.write(f"**تاريخ التسجيل (Date):** {p_date}")
                st.write(f"**الثمن الإجمالي (Prix Total):** {p_prix} DH")
                st.markdown("</div>", unsafe_allow_html=True)

                # --- وضعية الدفع والدفعات ---
                st.markdown("<hr style='border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)
                st.markdown("##### 💳 وضعية الدفع والدفعات:")
                
                hist = p.get('historique_paiements', [])
                if hist:
                    for i, pay in enumerate(hist):
                        st.markdown(f"🔹 **الدفعة {i+1}: {pay.get('montant')} DH** بتاريخ {pay.get('date')}")
                else:
                    st.caption("⚠️ لا توجد أي دفعة مسجلة.")

                # --- المجاميع لتحت كاع ---
                st.markdown("<br>", unsafe_allow_html=True)
                col_p1, col_p2 = st.columns(2)
                col_p1.metric("💰 مجموع المدفوع", f"{p_verse} DH")
                
                if p_reste > 0:
                    col_p2.metric("🔴 الباقي (Reste)", f"{p_reste} DH", delta=f"-{p_reste} DH", delta_color="inverse")
                else:
                    col_p2.metric("🟢 الباقي (Reste)", "0 DH", delta="Payé / خالص", delta_color="normal")


    # 3. مستطيل الوصولات (Bons)
with st.expander("🧾 الوصولات (Bons)", expanded=(st.session_state.get('section_ouverte') == 'bons')):
    bon_data = fetch_json("bons.json")
    if not bon_data:
        st.info("🔵 لا توجد وصولات مسجلة حالياً.")
    else:
        for idx, b in enumerate(bon_data):
            # 🎯 [تعديل فولاذي]: صنع معرف فريد (Unique ID) حتى لو غاب الـ id من السحاب
            # نستخدم مزيجاً من المورد، التاريخ، والمؤشر لضمان عدم التكرار مطلقاً
            b_id = b.get('id') or f"{b.get('vendeur')}_{b.get('date')}_{idx}"
            
            vendeur = b.get('vendeur', 'غير معروف')
            b_date = b.get('date', '---')
            b_tel = b.get('telephone', '---')
            b_ville = b.get('ville', '---')
            total = float(b.get('total', 0))
            verse = float(b.get('verse', 0))
            reste = float(b.get('reste', 0))
            
            with st.expander(f"🧾 بون: {vendeur} | المتبقي: {reste} DH"):
                
                # --- العنوان والبوطونات ---
                c1, c2, c3 = st.columns([2, 1, 1])
                with c1:
                    st.subheader("🧾 تفاصيل البون")
                with c2:
                   # --- تجهيز نص البون مفصل للوصولات ---
                    bon_text = f"========================================\n"
                    bon_text += f"          🧾 تفاصيل البون\n"
                    bon_text += f"========================================\n"
                    bon_text += f"المورد: {vendeur}\n"
                    bon_text += f"الهاتف: {b_tel}\n"
                    bon_text += f"المدينة: {b_ville}\n"
                    bon_text += f"تاريخ البون: {b_date}\n"
                    bon_text += f"========================================\n"
                    bon_text += f"          📦 السلع المشتراة\n"
                    bon_text += f"----------------------------------------\n"

                    # جلب السلع لي فـ البون
                    items = b.get('items', [])
                    if items:
                            for item in items:
                                bon_text += f"- {item.get('nom')} | الثمن: {item.get('prix')} DH\n"
                    else:
                         bon_text += "لا توجد سلع مسجلة.\n"

                    bon_text += f"----------------------------------------\n"
                    bon_text += f"الثمن الكلي المجموع: {total} DH\n"
                    bon_text += f"مجموع المدفوع: {verse} DH\n"
                    bon_text += f"الباقي (Reste): {reste} DH\n"
                    bon_text += f"========================================\n"
                    bon_text += f"          💳 سجل الدفعات\n"
                    bon_text += f"----------------------------------------\n"

                    # جلب الدفعات
                    hist = b.get('historique_paiements', [])
                    if hist:
                        for i, pay in enumerate(hist):
                            bon_text += f"الدفعة {i+1}: {pay.get('montant')} DH (بتاريخ: {pay.get('date')})\n"
                    else:
                         bon_text += "لا توجد أي دفعة مسجلة حالياً.\n"
                    bon_text += f"========================================\n"

                    st.download_button(
                        label="📥 حفظ", 
                        data=bon_text.encode('utf-8-sig'),  # هادي هي اللي كتقاد العربية
                        file_name=f"Bon_{vendeur}.txt", 
                        mime="text/plain; charset=utf-8",    # هادي هي اللي كتقاد القراءة فالتليفون
                        key=f"dl_bon_{b_id}" # 🎯 [تعديل فولاذي]: استخدام المعرف الفريد
                      )
                with c3:
                    # 🎯 [تعديل فولاذي]: منطق المسح بالهوية لضمان عدم حذف عنصر خاطئ
                    if st.button("🗑️ مسح", key=f"del_bon_{b_id}"):
                        # فلترة القائمة: نحتفظ بكل العناصر ما عدا العنصر الحالي (بالمقارنة الكاملة)
                        updated_bon_data = [item for item in bon_data if item != b]
                        if save_json("bons.json", updated_bon_data):
                            st.success("🗑️ تم المسح بنجاح!")
                            st.rerun()

                # --- المربع المنظم ديال المعلومات ---
                st.markdown("<div style='background-color: #f8f9fa; border: 2px dashed #17a2b8; padding: 15px; border-radius: 5px; font-family: monospace; color: #000;'>", unsafe_allow_html=True)
                st.write(f"**المورد (Vendeur):** {vendeur}")
                st.write(f"**الهاتف (Téléphone):** {b_tel}")
                st.write(f"**المدينة (Ville):** {b_ville}")
                st.write(f"**تاريخ البون (Date):** {b_date}")
                st.markdown("</div>", unsafe_allow_html=True)

                # --- السلع المشتراة وسط البون ---
                st.markdown("##### 📦 السلع المشتراة:")
                for item in b.get('items', []):
                    st.write(f"▪️ {item.get('nom')} | الثمن: **{item.get('prix')} DH**")

                # --- وضعية الدفع والدفعات ---
                st.markdown("<hr style='border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)
                st.markdown("##### 💳 وضعية الدفع والدفعات:")
                
                hist = b.get('historique_paiements', [])
                if hist:
                    for i, pay in enumerate(hist):
                        st.markdown(f"🔹 **الدفعة {i+1}: {pay.get('montant')} DH** بتاريخ {pay.get('date')}")
                else:
                    st.caption("⚠️ لا توجد أي دفعة مسجلة.")

                # --- المجاميع لتحت كاع ---
                st.markdown("<br>", unsafe_allow_html=True)
                col_p1, col_p2 = st.columns(2)
                col_p1.metric("💰 مجموع المدفوع", f"{verse} DH")
                
                if reste > 0:
                    col_p2.metric("🔴 الباقي (Reste)", f"{reste} DH", delta=f"-{reste} DH", delta_color="inverse")
                else:
                    col_p2.metric("🟢 الباقي (Reste)", "0 DH", delta="Payé / خالص", delta_color="normal")