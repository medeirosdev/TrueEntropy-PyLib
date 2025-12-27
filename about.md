1. A Estrutura Lógica (O Fluxo)
Imagine a biblioteca como uma usina de reciclagem de caos. O fluxo de dados será:

Os Coletores (Harvesters): Agentes independentes que ficam "ouvindo" o mundo. Eles não param.

O Misturador (The Mixer): Onde os dados crus entram. Aqui usamos criptografia para garantir que o dado de entrada altere o estado da piscina de forma irreversível.

A Piscina (The Pool): Um buffer de bytes (ex: 4096 bits) que representa o "estado atual do universo" segundo o computador.

O Extrator (The Tap): A função que o usuário chama. Ela retira entropia da piscina e entrega um número limpo (0.0 a 1.0).

2. Mapeamento das Fontes de Dados (De onde vamos tirar o caos?)
Para uma Lib Python que se preze, precisamos de fontes que funcionem em qualquer SO (Linux, Windows, Mac). Aqui estão os 4 pilares de dados que usaremos:

A. Fonte Cronológica (O Caos do Tempo)
Computadores tentam ser precisos, mas em níveis nanoscópicos, eles "tremen".

O Dado: O "Jitter" (tremulação) da execução do código.

Onde pegar: Diferença entre o time.perf_counter_ns() (relógio de alta precisão) antes e depois de uma operação simples (como criar uma lista vazia).

Por que funciona: O sistema operacional interrompe o processo o tempo todo (scheduling). A duração exata de uma operação simples nunca é igual duas vezes seguidas. É o caos do agendador da CPU.

B. Fonte de Rede (O Caos da Infraestrutura)
A internet é um sistema físico sujeito a temperatura, tráfego e colisões de pacotes.

O Dado: Latência de conexão (Ping).

Onde pegar: Fazer uma requisição HEAD leve para um servidor robusto (Google, Cloudflare) e medir o tempo de resposta até a casa dos decimais.

Por que funciona: O tempo que um elétron/fóton leva para viajar quilômetros de fibra ótica varia devido ao congestionamento da rede global. É o "clima" da internet.

C. Fonte de Sistema (O Caos do Hardware)
O estado interno da máquina muda milhares de vezes por segundo.

O Dado: Estatísticas voláteis do Sistema Operacional.

Onde pegar:

Uso exato de memória RAM livre (em bytes).

Número de processos ativos no momento.

Posição do ponteiro do mouse (se houver interface gráfica).

Tempo desde o último boot (uptime) em milissegundos.

Por que funciona: É impossível prever o número exato de bytes livres na RAM em um dado microssegundo, pois o SO está alocando e desalocando memória constantemente.

D. Fonte Externa (O Caos do Mundo - Opcional/API)
Conectar a lib a fenômenos naturais reais.

O Dado: Dados ambientais ao vivo.

Onde pegar: APIs públicas.

Sismologia: Última magnitude registrada (USGS).

Cripto: Preço do Bitcoin com 8 casas decimais (o mercado financeiro é um sistema caótico de psicologia humana).

Por que funciona: Traz entropia de fora da caixa do computador.

3. O Mecanismo da "Entropy Pool" (O Coração)
Não podemos apenas somar esses números. Precisamos de uma Função de Absorção.

A Estratégia de Mistura (Whitening): Cada vez que um dado novo chega (ex: latência de rede = 45ms), não guardamos "45". Nós pegamos o estado atual da piscina + o dado novo e aplicamos um Hash SHA-256.

Fórmula: Novo_Estado = SHA256(Estado_Anterior + Dado_Novo)

Isso garante que cada bit de entrada afete cada bit da piscina. Se a latência mudar de 45ms para 46ms, o resultado final muda completamente (efeito avalanche).

4. O Planejamento da Biblioteca (Modularidade)
Para disponibilizar no PIP, a estrutura deve ser pensada para que o usuário não precise configurar nada, mas possa configurar tudo se quiser.

Módulo Core (pool):

Gerencia o buffer de bytes.

Contém a função de Hashing.

Contém a proteção contra "esvaziamento" (se tirarmos muita entropia, a piscina bloqueia até coletar mais dados).

Módulo Coletores (harvesters):

Thread de Background: O ideal é que a lib tenha uma opção de rodar uma thread silenciosa que fica alimentando a piscina a cada X segundos com dados de rede/sistema. Assim, quando o usuário pedir um número, a piscina já está cheia.

Módulo Matemático (math):

Converte o Hash (hexadecimal) em:

Float (0.0 - 1.0) -> Probabilidade.

Booleano (True/False) -> Decisão.

Inteiro (Range A-B) -> Seleção.

5. O Diferencial "Místico"
Para sua lib ter apelo, adicione um método chamado entropy_health().

Ele retorna uma pontuação de 0 a 100 de quão "caótica" está a piscina no momento.

Se o computador estiver muito ocioso e sem internet, a "saúde" cai. Se estiver rodando muita coisa, a "saúde" sobe. Isso dá uma sensação de "vida" ao código.