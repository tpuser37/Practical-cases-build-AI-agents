import pandas as pd
import warnings
from transformers import pipeline
from sdv.metadata import Metadata
from sdv.single_table import GaussianCopulaSynthesizer, CTGANSynthesizer
from sdv.evaluation.single_table import (
    run_diagnostic,
    evaluate_quality,
    get_column_plot
)

warnings.filterwarnings("ignore")


# -----------------------------
# Load Data
# -----------------------------
def load_real_data(path, nrows=500):
    return pd.read_csv(path, nrows=nrows)


# -----------------------------
# Objective 1: Schema Replication
# -----------------------------
def schema_replication(real_data, num_rows=500):
    metadata = Metadata.detect_from_dataframe(real_data)
    synthesizer = GaussianCopulaSynthesizer(metadata)
    synthesizer.fit(real_data)
    return synthesizer.sample(num_rows), metadata


# -----------------------------
# Objective 2: Realism + Variety
# -----------------------------
def realism_and_variety(real_data, num_rows=500):
    metadata = Metadata.detect_from_dataframe(real_data)
    synthesizer = CTGANSynthesizer(metadata, epochs=300, verbose=False)
    synthesizer.fit(real_data)
    return synthesizer.sample(num_rows), metadata


# -----------------------------
# Objective 3: Narrative Fields (LLM-based)
# -----------------------------

def generate_narrative_fields(
    synthetic_data,
    column_name="CustomerReview",
    model_name="gpt2",
    prompt_column="PreferredOrderCat"  # colonne utilisée pour personnaliser le prompt
):
    """
    Génère du texte narratif pour chaque ligne du dataset synthétique
    en utilisant une colonne comme contexte pour le prompt.
    """
    generator = pipeline("text-generation", model=model_name, device=-1)  # CPU

    narratives = []

    for i, row in synthetic_data.iterrows():
        # Prompt dynamique selon le contenu de la ligne
        context_value = row[prompt_column]
        prompt = f"Write a short customer review about purchasing a {context_value} online."

        # Génération du texte
        output = generator(
            prompt,
            max_length=40,
            num_return_sequences=1,
            truncation=True
        )
        # On récupère le texte généré
        narratives.append(output[0]["generated_text"])

    # On ajoute la colonne narrative au dataset
    synthetic_data[column_name] = narratives
    return synthetic_data

# -----------------------------
# Diagnostics
# -----------------------------
def run_diagnostics(real_data, synthetic_data, metadata):
    return run_diagnostic(
        real_data=real_data,
        synthetic_data=synthetic_data,
        metadata=metadata
    )


# -----------------------------
# Quality Evaluation
# -----------------------------
def run_quality(real_data, synthetic_data, metadata):
    return evaluate_quality(
        real_data,
        synthetic_data,
        metadata
    )


# -----------------------------
# Column Quality Ranking
# -----------------------------
def show_column_quality(quality_report):
    print("\nColumns from highest to lowest quality score")
    print("------------------------------------------------")
    print(quality_report.get_details("Column Shapes"))


# -----------------------------
# Visualization
# -----------------------------
def visualize_column(real_data, synthetic_data, metadata, column_name):
    fig = get_column_plot(
        real_data=real_data,
        synthetic_data=synthetic_data,
        column_name=column_name,
        metadata=metadata
    )
    fig.show()


# -----------------------------
# MAIN
# -----------------------------
def main():
    real_data = load_real_data("Data/E-Commerce Dataset.csv")

    print("""
Select synthesis objective:
1. Schema replication
2. Realism + variety
3. Narrative fields
    """)
    choice = input("Your choice: ")

    if choice == "1":
        synthetic_data, metadata = schema_replication(real_data)

    elif choice == "2":
        synthetic_data, metadata = realism_and_variety(real_data)
    
    elif choice == "3":
        synthetic_data, metadata = realism_and_variety(real_data)
        synthetic_data = generate_narrative_fields(
            synthetic_data,
            column_name="CustomerReview",
            model_name="gpt2"
        )
    else:
        print("Invalid choice.")
        return

    # ✅ Always save CSV
    synthetic_data.to_csv('Data/synthetic_data.csv', index=False)
    print("Synthetic data saved to CSV.")

    # Post-generation menu
    quality_report = None

    while True:
        print("""
Post-generation actions:
1. Run diagnostic report
2. Run quality report
3. Show column quality ranking
4. Visualize a column
0. Exit
        """)

        action = input("Choice: ")

        if action == "1":
            run_diagnostics(real_data, synthetic_data, metadata)
            print("Diagnostic completed.")

        elif action == "2":
            quality_report = run_quality(real_data, synthetic_data, metadata)
            print("Overall quality score:", quality_report.get_score())

        elif action == "3":
            if quality_report is None:
                print("Quality report not generated yet. Generating now...")
                quality_report = run_quality(real_data, synthetic_data, metadata)
            show_column_quality(quality_report)

        elif action == "4":
            column = input("Column name to visualize: ")
            visualize_column(real_data, synthetic_data, metadata, column)

        elif action == "0":
            print("Exiting.")
            break

        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
