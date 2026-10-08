from dotenv import load_dotenv

import os



load_dotenv()



GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

import json

import re

from datetime import datetime

from pathlib import Path



import streamlit as st

from PIL import Image

import google.generativeai as genai



# ============================================================

# PURCHASEWISE

# Your brutally honest spending assistant

# ============================================================



APP_NAME = "PennyAnalyzer"

MODEL_NAME = "gemini-3.8-flash"

DATA_FILE = Path("purchasewise_data.json")



st.set_page_config(

    page_title=APP_NAME,

    page_icon="💸",

    layout="wide",

    initial_sidebar_state="expanded",

)



# -----------------------------

# Styling

# -----------------------------

st.markdown(

    """

    <style>

    .stApp {

        background: #0b0d12;

        color: #f4f4f5;

    }

    .block-container {

        max-width: 1150px;

        padding-top: 2rem;

        padding-bottom: 3rem;

    }

    .hero {

        padding: 1.4rem 1.5rem;

        border-radius: 20px;

        background: linear-gradient(135deg, #151a24, #10131a);

        border: 1px solid #252b38;

        margin-bottom: 1.2rem;

    }

    .hero h1 {

        margin-bottom: .2rem;

    }

    .muted {

        color: #a1a1aa;

    }

    .card {

        padding: 1rem;

        border-radius: 16px;

        background: #131720;

        border: 1px solid #252b38;

        margin-bottom: .8rem;

    }

    .decision {

        padding: 1.2rem;

        border-radius: 18px;

        background: #171b24;

        border: 1px solid #343b4b;

        margin-top: 1rem;

    }

    .small {

        font-size: .9rem;

        color: #a1a1aa;

    }

    div[data-testid="stMetric"] {

        background: #131720;

        border: 1px solid #252b38;

        padding: 12px;

        border-radius: 14px;

    }

    </style>

    """,

    unsafe_allow_html=True,

)



# -----------------------------

# Local data

# -----------------------------

DEFAULT_DATA = {

    "purchases": [],

    "bills": [],

    "buy_decisions": [],

    "settings": {

        "currency": "₹",

        "monthly_budget": 15000.0,

    },

}





def load_data():

    if not DATA_FILE.exists():

        return DEFAULT_DATA.copy()



    try:

        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))

        for key in DEFAULT_DATA:

            if key not in data:

                data[key] = DEFAULT_DATA[key]

        return data

    except Exception:

        return DEFAULT_DATA.copy()





def save_data():

    DATA_FILE.write_text(

        json.dumps(st.session_state.data, indent=2, ensure_ascii=False),

        encoding="utf-8",

    )





if "data" not in st.session_state:

    st.session_state.data = load_data()



if "api_key" not in st.session_state:

    st.session_state.api_key = ""



if "analysis_result" not in st.session_state:

    st.session_state.analysis_result = None



if "bill_result" not in st.session_state:

    st.session_state.bill_result = None



if "buy_result" not in st.session_state:

    st.session_state.buy_result = None





# -----------------------------

# Gemini helpers

# -----------------------------

def get_model():

    if not GEMINI_API_KEY:

        raise ValueError("Gemini API key is missing. Check your .env file.")



    genai.configure(api_key=GEMINI_API_KEY.strip())

    return genai.GenerativeModel(MODEL_NAME)





def extract_json(text):

    text = text.strip()



    if text.startswith("```"):

        text = re.sub(r"^```(?:json)?", "", text.strip(), flags=re.I)

        text = re.sub(r"```$", "", text.strip())
    match = re.search(r"\{.*\}", text, re.S)
    if not match:

        raise ValueError("The AI did not return valid JSON.")



    return json.loads(match.group(0))





def ask_gemini(image, prompt):

    model = get_model()

    response = model.generate_content([prompt, image])

    return response.text





# -----------------------------

# Utility calculations

# -----------------------------

def month_key(date_string):

    try:

        return datetime.fromisoformat(date_string).strftime("%Y-%m")

    except Exception:

        return datetime.now().strftime("%Y-%m")





def current_month():

    return datetime.now().strftime("%Y-%m")





def money(value):

    symbol = st.session_state.data["settings"].get("currency", "₹")

    return f"{symbol}{float(value):,.2f}"





def purchase_totals():

    purchases = [

        p for p in st.session_state.data["purchases"]

        if month_key(p.get("date", "")) == current_month()

    ]



    totals = {

        "all": 0.0,

        "essential": 0.0,

        "want": 0.0,

        "impulse": 0.0,

    }



    for p in purchases:

        amount = float(p.get("price", 0) or 0)

        category = str(p.get("category", "Want")).lower()



        totals["all"] += amount



        if category in ("essential", "useful"):

            totals["essential"] += amount

        elif category in ("impulse",):

            totals["impulse"] += amount

        else:

            totals["want"] += amount



    return totals





def bill_total():

    return sum(

        float(b.get("amount", 0) or 0)

        for b in st.session_state.data["bills"]

        if month_key(b.get("date", "")) == current_month()

    )





# ============================================================

# Sidebar navigation

# ============================================================

with st.sidebar:

    st.markdown("## 💸 PennyAnalyzer")

    st.caption("Your brutally honest spending assistant.")

    if "navigation" not in st.session_state:
        st.session_state.navigation = "🏠 Home"
    if "next_page" in st.session_state:
        st.session_state.navigation = st.session_state.pop("next_page")

    page = st.radio(

        "Navigate",

        [

            "🏠 Home",

            "📸 Scan Receipt",

            "💬 Ask Penny",

            "🏠 Essential Bills",

            "⚙️ Settings",

        ],

        label_visibility="collapsed",
        key="navigation",

    )



    st.divider()



    totals = purchase_totals()

    bills = bill_total()



    st.metric("This month's purchases", money(totals["all"]))

    st.metric("Essential bills", money(bills))





# ============================================================

# HOME

# ============================================================

if page == "🏠 Home":

    st.title("💸 PennyAnalyzer")
    st.caption("Know where your money goes — and think twice before the next purchase.")

    totals = purchase_totals()

    bills = bill_total()

    budget = float(st.session_state.data["settings"].get("monthly_budget", 15000))



    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Purchases", money(totals["all"]))

    col2.metric("Essential bills", money(bills))

    col3.metric("Wants + impulse", money(totals["want"] + totals["impulse"]))

    col4.metric("Total outflow", money(totals["all"] + bills))



    st.markdown("### What do you want to do?")



    a, b = st.columns(2)

    with a:
        with st.container(border=True):
            st.subheader("📸 Scan a receipt")
            st.caption("Upload a receipt and let AI extract items, prices and spending categories.")
            if st.button("Scan receipt →", use_container_width=True):
                st.session_state.next_page = "📸 Scan Receipt"
                st.rerun()

    with b:
        with st.container(border=True):
            st.subheader("💬 Ask Penny")
            st.caption("Chat about a purchase, explain what you need, and get a BUY, WAIT or SKIP opinion.")
            if st.button("Ask Penny →", use_container_width=True):
                st.session_state.next_page = "💬 Ask Penny"
                st.rerun()

    st.markdown("### 📊 This month")



    used = totals["all"] + bills

    remaining = budget - used



    st.progress(min(max(used / budget, 0.0), 1.0) if budget else 0.0)



    if remaining >= 0:

        st.success(

            f"You have {money(remaining)} left against your monthly budget of {money(budget)}."

        )

    else:

        st.error(

            f"You are {money(abs(remaining))} over your monthly budget of {money(budget)}."

        )



    st.info(

        "💡 Bills are tracked separately from discretionary purchases. "

        "Rent, electricity, gas and similar essentials should not be labelled "

        "as 'unnecessary' just because they are expensive."

    )



    st.markdown("### 🧠 Your spending split")



    split_cols = st.columns(3)

    split_cols[0].metric("Essentials", money(totals["essential"]))

    split_cols[1].metric("Wants", money(totals["want"]))

    split_cols[2].metric("Impulse", money(totals["impulse"]))



    if st.session_state.data["bills"]:
        st.markdown("### 🧾 Recent essential bills")
        recent = sorted(
            st.session_state.data["bills"],
            key=lambda x: x.get("date", ""),
            reverse=True,
        )[:5]

        for bill in recent:
            with st.container(border=True):
                st.write(f"**{bill.get('bill_type', 'Essential Bill')}** — {money(bill.get('amount', 0))}")
                st.caption(bill.get("date", ""))


# ============================================================
# RECEIPT SCANNER

# ============================================================

elif page == "📸 Scan Receipt":

    st.title("📸 Scan a Receipt")

    st.caption("Upload a grocery, clothing, restaurant, movie or shopping receipt.")



    uploaded = st.file_uploader(

        "Upload receipt",

        type=["jpg", "jpeg", "png", "webp"],

        key="receipt_upload",

    )



    if uploaded:

        image = Image.open(uploaded)

        st.image(image, caption="Receipt", width=600)



        if st.button("🔍 Analyze Receipt", type="primary"):

            with st.spinner("Reading your receipt..."):

                try:

                    prompt = """

                    Analyze this receipt carefully.



                    Return ONLY valid JSON in this exact structure:

                    {

                      "store": "store name",

                      "date": "YYYY-MM-DD",

                      "total": 0,

                      "items": [

                        {

                          "name": "item name",

                          "price": 0,

                          "category": "Essential|Want|Impulse"

                        }

                      ]

                    }



                    Rules:

                    - Essential = groceries, household necessities, required clothing,

                      medicines or other genuinely needed purchases.

                    - Want = normal discretionary purchases that are intentional.

                    - Impulse = snack/treat/random purchase that appears non-essential

                      or impulsive.

                    - Do not invent missing prices.

                    - Use 0 only when the price cannot be read.

                    """



                    raw = ask_gemini(image, prompt)

                    result = extract_json(raw)

                    st.session_state.analysis_result = result



                except Exception as e:

                    st.error(f"Analysis failed: {e}")



    result = st.session_state.analysis_result



    if result:

        st.divider()

        st.subheader("Purchase Analysis")



        c1, c2, c3 = st.columns(3)

        c1.metric("Store", result.get("store", "Unknown"))

        c2.metric("Receipt total", money(result.get("total", 0)))

        c3.metric("Items", len(result.get("items", [])))



        rows = []



        for item in result.get("items", []):

            rows.append(

                {

                    "Item": item.get("name", "Unknown"),

                    "Price": money(item.get("price", 0)),

                    "Category": item.get("category", "Want"),

                }

            )



            st.session_state.data["purchases"].append(

                {

                    "date": result.get("date") or datetime.now().isoformat(),

                    "store": result.get("store", "Unknown"),

                    "item": item.get("name", "Unknown"),

                    "price": float(item.get("price", 0) or 0),

                    "category": item.get("category", "Want"),

                }

            )



        if rows:

            st.dataframe(rows, use_container_width=True, hide_index=True)



        total = float(result.get("total", 0) or 0)

        impulse = sum(

            float(x.get("price", 0) or 0)

            for x in result.get("items", [])

            if str(x.get("category", "")).lower() == "impulse"

        )

        wants = sum(

            float(x.get("price", 0) or 0)

            for x in result.get("items", [])

            if str(x.get("category", "")).lower() == "want"

        )



        st.markdown("### 🤨 Brutally Honest Opinion")



        if total and (impulse + wants) / total > 0.30:

            st.warning(

                f"**WAIT.** About {((impulse + wants) / total) * 100:.0f}% of this "

                "receipt is discretionary spending. The essentials look fine, "

                "but the wants/impulse items are where you should be careful."

            )

        else:

            st.success(

                "🟢 **Looks reasonable.** Most of this purchase appears to be essential "

                "or intentional rather than impulsive."

            )



        save_data()



        # Prevent duplicate saving if Streamlit reruns after this point.

        st.session_state.analysis_result = None





# ============================================================

# ASK PENNY — CHAT-BASED PURCHASE ADVISOR
# ============================================================
elif page == "💬 Ask Penny":
    st.title("💬 Ask Penny")
    st.caption("Tell Penny what you want, why you want it, your budget, and anything you are unsure about.")

    if "penny_chat" not in st.session_state:
        st.session_state.penny_chat = [{
            "role": "assistant",
            "content": (
                "Hey! I'm Penny 👋 Tell me what you're thinking of buying. "
                "Include the price, what you need it for, your budget, and "
                "whether you already own something similar. I'll be honest — BUY, WAIT, or SKIP."
            ),
        }]
    if "penny_image" not in st.session_state:
        st.session_state.penny_image = None

    with st.expander("📷 Add a product screenshot (optional)"):
        product_image = st.file_uploader("Attach a product image", type=["jpg", "jpeg", "png", "webp"], key="penny_product_image")
        if product_image:
            st.session_state.penny_image = Image.open(product_image).copy()
            st.image(st.session_state.penny_image, caption="Attached product", width=420)
            if st.button("Remove image"):
                st.session_state.penny_image = None
                st.rerun()

    for message in st.session_state.penny_chat:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_message = st.chat_input("Message Penny…")
    if user_message:
        st.session_state.penny_chat.append({"role": "user", "content": user_message})
        with st.chat_message("user"):
            st.markdown(user_message)

        # Keep simple greetings conversational and local. This also avoids
        # wasting an API request just because the user said hello.
        casual_replies = {
            "hi": "Hii 👋😊 What's up? Tell me what you're thinking about — a purchase, a budget, or anything you're unsure about.",
            "hii": "Hii hii 👋💛 What are we figuring out today?",
            "hello": "Heyyy! 👋 I'm Penny. What are you thinking about?",
            "hey": "Hey! 👋 What's on your mind?",
            "heyy": "Heyyy 👋 Tell me everything — what are we deciding today?",
        }
        casual_key = re.sub(r"[^a-z]", "", user_message.lower())

        with st.chat_message("assistant"):
            if casual_key in casual_replies:
                answer = casual_replies[casual_key]
                st.markdown(answer)
                st.session_state.penny_chat.append({"role": "assistant", "content": answer})
            else:
                with st.spinner("Penny is thinking..."):
                    try:
                        model = get_model()
                        recent = st.session_state.data["purchases"][-50:]
                        history = st.session_state.penny_chat[-12:]
                        prompt = f"""
You are Penny, a warm, natural, conversational AI purchase companion inside PennyAnalyzer.
Talk like a helpful friend having a real chat, not like a form or a report.
If the user is just greeting you or making casual conversation, respond naturally and do not force a purchase verdict.
If they are talking about a purchase, understand what they need before judging it. Ask follow-up questions naturally when useful.
When there is enough information to make a decision, clearly state **VERDICT: BUY**, **VERDICT: WAIT**, or **VERDICT: SKIP**, followed by concise reasoning and one practical next step.
Never shame the user. You are not a financial adviser. Necessary purchases should not be discouraged just because they are expensive.
Consider need, price, budget, impulse signals, duplicates and recent purchases. If an image is attached, use it.

Recent purchase history:
{json.dumps(recent, ensure_ascii=False)}

Conversation so far:
{json.dumps(history, ensure_ascii=False)}
"""
                        contents=[prompt]
                        if st.session_state.penny_image is not None:
                            contents.append(st.session_state.penny_image)
                        contents.append(user_message)
                        response = model.generate_content(contents)
                        answer = response.text.strip()
                        st.markdown(answer)
                        st.session_state.penny_chat.append({"role": "assistant", "content": answer})
                        verdict = re.search(r"VERDICT\s*:\s*(BUY|WAIT|SKIP)", answer, re.I)
                        if verdict:
                            st.session_state.data["buy_decisions"].append({
                                "date": datetime.now().isoformat(),
                                "product": user_message[:100],
                                "verdict": verdict.group(1).upper(),
                                "price": 0,
                            })
                            save_data()
                    except Exception as e:
                        st.error(f"I couldn't analyze that right now: {e}")

    if len(st.session_state.penny_chat)>1 and st.button("🧹 Start a new chat"):
        st.session_state.penny_chat=[{"role":"assistant","content":"Fresh start 👋 What are you thinking of buying?"}]
        st.session_state.penny_image=None
        st.rerun()


# ============================================================


# ============================================================

elif page == "🏠 Essential Bills":

    st.title("🏠 Essential Bills")

    st.caption(

        "Track recurring or unavoidable household expenses separately from "

        "shopping and impulse spending."

    )



    st.info(

        "Use this for electricity, water, gas, internet, phone bills, rent, "

        "EMIs and other essential commitments. These are **not** treated as "

        "unnecessary purchases."

    )



    tab1, tab2 = st.tabs(["➕ Add / Scan Bill", "📋 Bill History"])



    with tab1:

        bill_image = st.file_uploader(

            "Upload a bill",

            type=["jpg", "jpeg", "png", "webp"],

            key="bill_upload",

        )



        if bill_image:

            image = Image.open(bill_image)

            st.image(image, caption="Bill", width=600)



            if st.button("🔍 Read Bill", type="primary"):

                with st.spinner("Reading your bill..."):

                    try:

                        prompt = """

                        Analyze this bill.



                        Return ONLY valid JSON:

                        {

                          "bill_type": "Electricity|Gas|Water|Internet|Phone|Rent|EMI|Other",

                          "provider": "provider name",

                          "date": "YYYY-MM-DD",

                          "amount": 0,

                          "due_date": "YYYY-MM-DD or blank",

                          "recurring": true

                        }



                        Do not invent values that cannot be read.

                        """



                        raw = ask_gemini(image, prompt)

                        st.session_state.bill_result = extract_json(raw)



                    except Exception as e:

                        st.error(f"Bill analysis failed: {e}")



        if st.session_state.bill_result:

            bill = st.session_state.bill_result



            st.subheader("Bill detected")



            c1, c2, c3 = st.columns(3)

            c1.metric("Type", bill.get("bill_type", "Other"))

            c2.metric("Amount", money(bill.get("amount", 0)))

            c3.metric("Provider", bill.get("provider", "Unknown"))



            if st.button("✅ Add this bill"):

                st.session_state.data["bills"].append(

                    {

                        "date": bill.get("date") or datetime.now().isoformat(),

                        "bill_type": bill.get("bill_type", "Other"),

                        "provider": bill.get("provider", "Unknown"),

                        "amount": float(bill.get("amount", 0) or 0),

                        "due_date": bill.get("due_date", ""),

                        "recurring": bool(bill.get("recurring", False)),

                    }

                )

                save_data()

                st.session_state.bill_result = None

                st.success("Bill added to your essential expenses.")

                st.rerun()



        st.divider()

        st.subheader("Add manually")



        with st.form("manual_bill"):

            bill_type = st.selectbox(

                "Bill type",

                ["Electricity", "Gas", "Water", "Internet", "Phone", "Rent", "EMI", "Other"],

            )

            provider = st.text_input("Provider / description")

            amount = st.number_input("Amount", min_value=0.0, step=100.0)

            date = st.date_input("Bill date")

            recurring = st.checkbox("Recurring bill")



            submitted = st.form_submit_button("Add bill")



            if submitted:

                st.session_state.data["bills"].append(

                    {

                        "date": date.isoformat(),

                        "bill_type": bill_type,

                        "provider": provider or bill_type,

                        "amount": amount,

                        "due_date": "",

                        "recurring": recurring,

                    }

                )

                save_data()

                st.success("Bill added.")



    with tab2:

        bills = st.session_state.data["bills"]



        if not bills:

            st.info("No bills added yet.")

        else:

            rows = [

                {

                    "Date": b.get("date", ""),

                    "Type": b.get("bill_type", "Other"),

                    "Provider": b.get("provider", ""),

                    "Amount": money(b.get("amount", 0)),

                    "Recurring": "Yes" if b.get("recurring") else "No",

                }

                for b in sorted(bills, key=lambda x: x.get("date", ""), reverse=True)

            ]



            st.dataframe(rows, use_container_width=True, hide_index=True)



            st.metric("All recorded essential bills", money(sum(

                float(b.get("amount", 0) or 0) for b in bills

            )))





# ============================================================

# SETTINGS
# ============================================================
elif page == "⚙️ Settings":

    # Settings is split into small screens so the main page stays clean.
    if "settings_view" not in st.session_state:
        st.session_state.settings_view = "main"

    settings_view = st.session_state.settings_view

    if settings_view == "main":
        st.title("⚙️ Settings")
        st.caption("Manage your budget preferences, privacy, data and app information.")

        st.divider()

        st.subheader("💰 Money")
        st.caption("Choose your currency and set your monthly spending budget.")
        if st.button("💰 Money Settings →", use_container_width=True):
            st.session_state.settings_view = "money"
            st.rerun()

        st.divider()

        st.subheader("🔐 Privacy & Legal")
        c1, c2 = st.columns(2)

        with c1:
            if st.button("🔐 Privacy Policy →", use_container_width=True):
                st.session_state.settings_view = "privacy"
                st.rerun()

            if st.button("📜 Terms & Conditions →", use_container_width=True):
                st.session_state.settings_view = "terms"
                st.rerun()

        with c2:
            if st.button("⚠️ AI & Financial Disclaimer →", use_container_width=True):
                st.session_state.settings_view = "disclaimer"
                st.rerun()

            if st.button("🗑️ Data Controls →", use_container_width=True):
                st.session_state.settings_view = "data"
                st.rerun()

        st.divider()

        st.subheader("ℹ️ About PennyAnalyzer")
        st.caption(
            f"PennyAnalyzer · Gemini model: {MODEL_NAME}\n\n"
            "Your brutally honest AI spending assistant."
        )

        st.info(
            "🔑 Your Gemini API key is loaded automatically from your .env file. "
            "You do not need to enter it in Settings."
        )

    elif settings_view == "money":
        st.title("💰 Money Settings")
        st.caption("Customize the way PennyAnalyzer tracks your money.")

        currency = st.selectbox(
            "Currency",
            ["₹", "$", "€", "£"],
            index=["₹", "$", "€", "£"].index(
                st.session_state.data["settings"].get("currency", "₹")
            ),
        )

        budget = st.number_input(
            "Monthly budget",
            min_value=0.0,
            value=float(
                st.session_state.data["settings"].get("monthly_budget", 15000)
            ),
            step=500.0,
        )

        if st.button("💾 Save Money Settings", type="primary"):
            st.session_state.data["settings"]["currency"] = currency
            st.session_state.data["settings"]["monthly_budget"] = budget
            save_data()
            st.success("Money settings saved.")

        st.divider()
        if st.button("← Back to Settings"):
            st.session_state.settings_view = "main"
            st.rerun()

    elif settings_view == "privacy":
        st.title("🔐 Privacy Policy")

        st.markdown(
            """
            **What we collect:** PennyAnalyzer processes receipt, product and bill
            images that you voluntarily upload, plus the spending information
            extracted from them.

            **Why we use it:** The information is used to analyze purchases,
            categorize spending, track bills and provide spending suggestions.

            **Your data:** The app does not intentionally sell or rent your personal
            information. The local version stores spending records in the app's
            local data file.

            **AI processing:** Uploaded images may be sent to Google's Gemini API
            for analysis. Do not upload documents containing information you do not
            want processed by an external AI service.

            **Security:** Never share your Gemini API key with another person or
            commit it to GitHub. Use environment variables or Streamlit secrets
            when deploying the application.

            **Control:** You can remove your locally stored PennyAnalyzer data by
            deleting `purchasewise_data.json`.
            """
        )

        st.divider()
        if st.button("← Back to Settings"):
            st.session_state.settings_view = "main"
            st.rerun()

    elif settings_view == "terms":
        st.title("📜 Terms & Conditions")

        st.markdown(
            """
            **1. Personal-use tool**

            PennyAnalyzer is a personal budgeting and spending-assistance tool.

            **2. No financial guarantee**

            AI recommendations are suggestions, not professional financial advice.
            PennyAnalyzer does not guarantee savings, profits or financial outcomes.

            **3. User responsibility**

            You are responsible for checking extracted receipt/bill information
            before relying on it.

            **4. AI limitations**

            AI can misunderstand images, prices, products or context. A BUY, WAIT
            or SKIP recommendation should not be treated as a financial decision
            made on your behalf.

            **5. Third-party services**

            AI processing may rely on third-party services such as Google's Gemini
            API. Their own terms and privacy practices may apply.

            **6. No liability for personal financial decisions**

            The creators are not responsible for losses, missed payments,
            incorrect categorization or purchasing decisions made using the app.

            **7. Intellectual property**

            Users retain rights to their own uploaded content. The app should not
            be used to upload material that the user does not have permission to
            process.

            **8. Changes**

            Features, policies and these terms may be updated as the application
            develops.

            **9. Governing law**

            For a public/commercial release, the final legal terms should be
            reviewed and adapted to the applicable laws and jurisdiction.
            """
        )

        st.divider()
        if st.button("← Back to Settings"):
            st.session_state.settings_view = "main"
            st.rerun()

    elif settings_view == "disclaimer":
        st.title("⚠️ AI & Financial Disclaimer")

        st.warning(
            "PennyAnalyzer is an educational/personal budgeting assistant. "
            "It is not a bank, financial adviser, accountant or payment service. "
            "Always verify bills, totals and recommendations yourself."
        )

        st.divider()
        if st.button("← Back to Settings"):
            st.session_state.settings_view = "main"
            st.rerun()

    elif settings_view == "data":
        st.title("🗑️ Data Controls")
        st.caption("Manage the spending records stored locally by PennyAnalyzer.")

        st.warning(
            "Deleting your local data removes your saved purchases, bills and "
            "BUY/WAIT/SKIP decisions from the app's local data file."
        )

        if st.button("🗑️ Delete All Local PennyAnalyzer Data", type="secondary"):
            st.session_state.data = DEFAULT_DATA.copy()
            save_data()
            st.success("Local PennyAnalyzer data has been reset.")

        st.divider()
        if st.button("← Back to Settings"):
            st.session_state.settings_view = "main"
            st.rerun()
