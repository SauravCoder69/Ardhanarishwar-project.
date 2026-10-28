# Ardhanarishwar AI — Project Guide

Yeh document project ke **abhi ke code** ke hisaab se app ka workflow, features aur technologies samjhata hai.

## Project kya karta hai?

Ardhanarishwar ek Streamlit web app hai jo candidates ko approved jobs dhoondhne, applications track karne aur career preparation mein madad karta hai. Admin job listings review, users aur analytics manage kar sakta hai.

## App ka end-to-end workflow

1. **App start hota hai:** Streamlit `app.py` chalata hai. Startup par SQLite database/tables initialize hote hain aur UI styling apply hoti hai.
2. **Login ya registration:** Login username/password se hota hai. Registration form se sirf **Candidate** account banta hai; Admin signup form nahi hai.
3. **Role ke mutabik navigation:** Candidate ko Dashboard, Find Jobs, My Applications aur My Profile milte hain. Admin ko Dashboard, Job Management, Analytics, User Management aur Settings milte hain.
4. **Admin listings review karta hai:** Admin Job Management mein Arbeitnow se listings refresh karta hai. Nayi listings pending review hoti hain; approve karne par hi candidate Find Jobs mein dikhengi. Rejected aur closed listings candidates ko nahi dikhengi.
5. **Candidate jobs dekhta aur track karta hai:** Find Jobs approved listings ko keyword aur job-type se filter karta hai. Candidate employer ki original site par apply karta hai, phir chahe toh My Applications mein listing save karke apna status track karta hai. App external employer ko application submit nahi karti.
6. **Candidate career tools use karta hai:** My Profile mein Career assistant, Career guidance/skill-gap roadmap, Resume & ATS, Interview practice aur Account security tabs hain. Interview practice ke liye resume aur job description upload hote hain; AI unke basis par sawal aur feedback banata hai. Uploads database mein save nahi hote.
7. **Admin ka kaam:** Job Management mein external listings refresh/approve/reject/close; Analytics mein usage aur feedback; User Management mein accounts; Settings mein password aur local Ollama status manage hota hai.
8. **Data save hota hai:** Accounts, profiles, chats, resume/interview records, jobs aur candidate application tracking SQLite mein rehte hain.

## Roles aur Admin account

- Public Register form **Candidate** account hi banata hai.
- Project koi default/demo admin credentials nahi banata. Naya Admin banane ke liye project folder se `python -m database.create_admin AnkitJha` chalayein; `AnkitJha` ko apne chosen, unused username se replace karein. Command display name aur kam-se-kam 12-character password prompt karega.
- Admin password reset karne ke liye README mein diya gaya `python -m database.reset_admin_password <username>` command istemal hota hai. Reset tabhi chalega jab username ka Admin account pehle se maujood ho.
- Business role ke accounts UI mein supported nahi hain; app unke liye workspace unavailable batata hai.

## Technologies — kya aur kyun?

| Technology | Project mein kaam |
|---|---|
| **Python** | App logic, integrations aur data processing. |
| **Streamlit** | Python se web UI, forms, navigation, tables aur dashboard banana. |
| **SQLite** | Local database: users, roles, profiles, conversations, jobs, applications aur activity records. |
| **Argon2id** | Password ko plain text ke bajay secure hash ke roop mein rakhna. |
| **Ollama** | Configured LLM endpoint par career assistant, roadmap, counselling aur resume/JD-based interview practice chalana. Default endpoint local hai aur model `llama3.2:1b` hai. Ollama na mile toh kuch requests fallback response deti hain. |
| **LangGraph** | AI request ko specialist agents ke flow se route/execute karna; available na ho toh direct agent fallback hai. |
| **Arbeitnow public API + Requests** | Job listings fetch karna. Abhi first page fetch hota hai; source adapter se integration alag rakhi gayi hai. |
| **PyMuPDF / python-docx** | Interview resume/JD aur ATS inputs se PDF/DOCX text nikalna; TXT bhi supported hai. |
| **Pandas / Plotly** | Career skill-gap visualization aur charts dikhana. |

## Project chalana

Project root (`Ardhnarishwar`) mein PowerShell ya terminal kholkar:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Terminal mein diya local URL browser mein kholein. LLM responses ke liye Ollama install/run karke model pull karna optional hai; Settings screen status batati hai. Ollama unavailable hone par app kuch AI features mein fallback responses dikhata hai. Job refresh ke liye internet connection chahiye.

## Important limitations

- Job listings external provider se aati hain; availability aur details provider par depend karte hain. Abhi refresh mein API ka first page fetch hota hai.
- External listing kholna application submit nahi karta; application statuses candidate khud track karta hai.
- Mock interview score AI-generated guidance hai, formal hiring assessment nahi.
- Resume/JD analysis ke liye `My Profile → Resume & ATS` use karein. Career Counselling module ka code maujood ho sakta hai, par uska tab current profile UI mein nahi dikhaya jata.

## Tests

Security aur data-integrity tests chalane ke liye project root se:

```powershell
python -m unittest discover -s tests -v
```
