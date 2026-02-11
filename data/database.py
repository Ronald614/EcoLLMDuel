import streamlit as st
from sqlalchemy import text
from typing import Dict, Any
import pandas as pd

conn = st.connection("evaluations_db", type="sql", url=st.secrets["DATABASE_URL"])

def verificar_perfil(email):
    email_tratado = email.lower().strip()
    try:
        df = conn.query(
            "SELECT * FROM user_profiles WHERE email = :email",
            params={"email": email_tratado},
            ttl=0,
            show_spinner=False
        )
        if not df.empty:
            return df.iloc[0].to_dict()
        else:
            return None
    except Exception as e:
        return None

def salvar_perfil_novo(dados):
    try:
        dados["email"] = dados["email"].lower().strip()
        query = text("""
            INSERT INTO user_profiles (
                email, name, institution, profession, age, gender,
                works_environmental_area, has_forest_management_exp,
                has_animal_monitoring_exp, has_camera_trap_exp
            ) VALUES (
                :email, :name, :institution, :profession, :age, :gender,
                :works_environmental_area, :has_forest_management_exp,
                :has_animal_monitoring_exp, :has_camera_trap_exp
            )
            ON CONFLICT (email) DO UPDATE SET
                name = EXCLUDED.name,
                institution = EXCLUDED.institution,
                profession = EXCLUDED.profession,
                age = EXCLUDED.age,
                gender = EXCLUDED.gender,
                works_environmental_area = EXCLUDED.works_environmental_area,
                has_forest_management_exp = EXCLUDED.has_forest_management_exp,
                has_animal_monitoring_exp = EXCLUDED.has_animal_monitoring_exp,
                has_camera_trap_exp = EXCLUDED.has_camera_trap_exp
        """)

        with conn.session as s:
            s.execute(query, dados)
            s.commit()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar perfil: {e}")
        return False

def salvar_avaliacao(dados: Dict[str, Any]) -> bool:
    try:
        query = text("""
            INSERT INTO evaluations (
                evaluator_email, image_path, image_id, species,
                model_a, model_b,
                time_a, time_b, text_len_a, text_len_b,
                model_response_a, model_response_b,
                result_code, comments,
                prompt, temperature
            ) VALUES (
                :evaluator_email, :image_path, :image_id, :species,
                :model_a, :model_b,
                :time_a, :time_b, :text_len_a, :text_len_b,
                :model_response_a, :model_response_b,
                :result_code, :comments,
                :prompt, :temperature
            )
        """)

        parametros = {
            "evaluator_email": dados["evaluator_email"],
            "image_path": dados["image_name"],
            "image_id": dados["image_id"],
            "species": dados["species_folder"],
            "model_a": dados["model_a"],
            "model_b": dados["model_b"],
            "time_a": dados["time_a"],
            "time_b": dados["time_b"],
            "text_len_a": dados["text_len_a"],
            "text_len_b": dados["text_len_b"],
            "model_response_a": dados["model_response_a"],
            "model_response_b": dados["model_response_b"],
            "result_code": dados["result_code"],
            "comments": dados["comments"],
            "prompt": dados["prompt"],
            "temperature": dados["temperature"]
        }

        with conn.session as s:
            s.execute(query, parametros)
            s.commit()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar avaliação: {e}")
        return False

def carregar_dados_duelos():
    try:
        query = "SELECT model_a, model_b, result_code, species, model_response_a, model_response_b FROM evaluations"
        df = conn.query(query, ttl=0, show_spinner=False)
        return df
    except Exception as e:
        return pd.DataFrame()