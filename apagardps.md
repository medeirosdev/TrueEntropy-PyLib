Lista de Melhorias para TrueEntropy
Novas Fontes de Entropia
MouseHarvester - Movimento e cliques do mouse (quando disponível)
AudioHarvester - Ruído do microfone (entropia de ruído ambiente)
WeatherHarvester - API OpenWeatherMap (temperatura, umidade, pressão)
RadioactiveHarvester - Integração com random.org (decaimento radioativo)
BlockchainHarvester - Últimos hashes de blocos Bitcoin/Ethereum
Novos Métodos de Geração
random_uuid() - Gerar UUIDs verdadeiramente aleatórios
random_password(length, charset) - Gerador de senhas seguras
random_token() - Tokens hexadecimais/base64
weighted_choice(seq, weights) - Escolha ponderada
triangular(low, high, mode) - Distribuição triangular
exponential(lambda) - Distribuição exponencial
Performance & Arquitetura
Async support - await trueentropy.random_async() para aplicações async
Pool persistence - Salvar/restaurar estado do pool entre execuções
Multiple pools - Suporte a múltiplos pools isolados
Lazy harvester loading - Carregar harvesters sob demanda
Cython acceleration - Compilar partes críticas em C
Qualidade & Segurança
NIST SP 800-90B compliance - Testes de qualidade de entropia
Entropy estimation improvements - Estimativas mais precisas por fonte
Secure memory wiping - Limpar memória sensível após uso
Logging configurável - Logs detalhados para debugging
Developer Experience
CLI tool - trueentropy generate --int 1 100
Streaming API - Gerar entropia infinita como iterator
Benchmark suite - Comparar com 
random
, secrets, etc.
Documentation site - MkDocs com exemplos interativos
GitHub Actions CI - Testes automáticos em cada PR
Integrações
NumPy compatibility - trueentropy.numpy.random(shape)
Pandas integration - Gerar DataFrames aleatórios
Django/Flask helpers - Decorators e middleware
Jupyter widget - Visualização do pool em tempo real