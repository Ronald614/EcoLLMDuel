import matplotlib.pyplot as plt

# Espécies e número de amostras
especies = [
    'Crax globulosa',
    'Didelphis albiventris',
    'Leopardus wiedii',
    'Panthera onca',
    'Pauxi tuberosa',
    'Sapajus macrocephalus',
    'Sciurus spadiceus',
    'Tupinambis teguixin',
    'Background (Sem espécie)'
]

quantidades = [3444, 4, 2446, 5161, 5350, 2159, 45, 4344, 5046]

# Figura
plt.figure(figsize=(14, 6))

# Gráfico de barras
bars = plt.bar(especies, quantidades)

# Rótulos e título
plt.xlabel('Espécies')
plt.ylabel('Número de amostras')
plt.title('Distribuição de amostras por espécies')

plt.xticks(rotation=30, ha='right')

# Valores acima de cada barra
for bar in bars:
    altura = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        altura,
        f'{int(altura)}',
        ha='center',
        va='bottom',
        fontsize=9
    )

plt.tight_layout()
plt.show()
