# Lucky Mod 🐶

Um mod para **Minecraft 1.7.10 (Forge)** que adiciona o **Lucky**, um cachorrinho preto de peito, patas,
franjinha e ponta do rabo brancos. Ele vem com o modpack **faafPack Beta 1.7.10**, que deixa o jogo com a
cara e a iluminação do Minecraft Beta 1.7.3.

## O que o Lucky faz

| Ação | Como |
| --- | --- |
| Chamar o Lucky | Use a **Caminha do Lucky** (clique direito). Ele já chega domesticado por você. |
| Fazer carinho | Clique direito nele (ele abana o rabo, inclina a cabeça e solta corações). |
| Sentar / levantar | **Shift + clique direito** (só o dono). |
| Tosar | Clique direito segurando uma **tesoura**. O pelo volta depois de 20 minutos (configurável). |
| Curar | Dê carne quando ele estiver machucado. |

- Duas aparências: **peludo** (Cairn Terrier) e **tosado** (corpo de Chihuahua com o rostinho do Cairn),
  adaptadas do resource pack Better Dogs do MrBlueYeti.
- Latidos de verdade: um normal e um bravo (com rosnado) quando ele está brigando.
- Por padrão ele é imortal: não morre, não se afoga e volta para perto do dono se cair no void.
  Para removê-lo, um jogador no criativo precisa bater nele agachado.

### Receita da Caminha do Lucky

```
[ lã preta ] [ lágrima de ghast ] [ lã preta ]
[ lã preta ] [ fatia de melancia ] [ lã preta ]
[ lã preta ] [     lã preta      ] [ lã preta ]
```

### Configuração

Fica em `config/luckymod.cfg` (é criado ao abrir o jogo pela primeira vez):

- `immortal`: se o Lucky pode morrer ou não.
- `furRegrowMinutes`: quanto tempo o pelo leva para voltar depois da tosa (1 a 1440, padrão 20).

## Instalação

### Opção 1: o modpack completo (recomendado)

1. Instale o [Prism Launcher](https://prismlauncher.org/download/) e entre com a sua conta da Microsoft.
2. Baixe o `faafPack_Beta1.7.10.zip` na página de [Releases](../../releases/latest).
3. No Prism, clique em **Add Instance → Import**, escolha o `.zip` e clique em **OK**.
4. O Minecraft 1.7.10 precisa do **Java 8**. Se o Prism reclamar do Java, abra a instância em
   **Edit → Settings → Java** e clique em **Auto-detect** ou **Download Java** (escolha a versão 8).
5. Clique em **Launch**.

Já vem tudo configurado: mods, configs, OptiFine e resource packs. Se a iluminação não parecer a da Beta, confira:

- **Options → Resource Packs**: `Beta173 Lighting` precisa estar ativo e **acima** do `old-lighting-old-water`.
- **Options → Video Settings → Quality → Custom Colors**: ON.

### Opção 2: só o mod

1. Instale o **Forge 1.7.10-10.13.4.1614** (qualquer launcher serve).
2. Baixe o `luckymod-x.y.z.jar` em [Releases](../../releases/latest).
3. Coloque o arquivo na pasta `mods` do jogo.

Para ver os modelos novos não é preciso nenhum resource pack: tudo vai dentro do `.jar`.

## O que tem no modpack

Minecraft 1.7.10 + Forge 10.13.4.1614, com:

| Mod | Para quê |
| --- | --- |
| Lucky Mod | o Lucky 🐶 |
| OptiFine HD U D6 | desempenho e a iluminação customizada |
| Nostalgia Generator | geração de mundo da Beta |
| The Aether + Gilded Games Util | a dimensão do Aether |
| Mo' Creatures + Custom Mob Spawner | bichos |
| Hunger Strike | fome no estilo Beta |
| Better Sprinting, BetterFps, FastCraft | conforto e desempenho |
| Not Enough Items + CodeChickenCore/Lib | ver receitas |

Resource packs: `Beta173 Lighting` (feito para este pack), `Old Default Beta Edition`,
`old-lighting-old-water`, `Aether b1.7.3 Textures` e Golden Days.

Todos os mods e resource packs de terceiros pertencem aos seus autores. Eles estão no `.zip` apenas para
facilitar a instalação entre amigos. A pasta [`modpack/`](modpack) do repositório guarda só as configurações e o
resource pack de iluminação.

## Para quem quer mexer

### Repintar o Lucky

1. Abra `blockbench/Lucky_peludo.bbmodel` ou `blockbench/Lucky_tosado.bbmodel` no [Blockbench](https://www.blockbench.net/).
2. Na aba **Paint**, pinte direto no modelo 3D.
3. Salve a textura (clique direito em `lucky.png` → **Save**). Ela é gravada direto em
   `src/main/resources/assets/luckymod/textures/entity/lucky.png`.
4. Recompile (veja abaixo).

A cabeça, as orelhas e o rabo usam os mesmos pixels nas duas aparências. Mude só os pixels: o formato dos
cubos vem do código (`LuckyRigs.java`), não do `.bbmodel`.

### Compilar

Precisa do JDK 21 ou mais novo (o build usa o toolchain do GTNH, que baixa o Java 8 sozinho).

```bash
VERSION=1.8.1 ./gradlew build
```

O jar fica em `build/libs/luckymod-1.8.1.jar` (use o que **não** termina em `-dev` ou `-sources`).

### Ferramentas

- `tools/gen_betterdogs.py`: converte os modelos do Better Dogs no `LuckyRigs.java` e nos `.bbmodel`.
  Uso: `python tools/gen_betterdogs.py <pasta do Better Dogs extraído> <pasta de prévias>`.
  Só reescreve a textura se receber `--texture` (isso apagaria a pintura feita à mão).
- `tools/gen_beta_lightmap.py`: gera o resource pack `Beta173 Lighting` com a curva de luz da Beta 1.7.3.

## Créditos

- Modelos do cachorro adaptados do Better Dogs, de MrBlueYeti.
- Mod e modpack: GCLemos.
