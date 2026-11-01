# chatbot-whatsapp

Chatbot de atendimento para WhatsApp que responde dúvidas consultando uma base de conhecimento
(RAG: busca os trechos mais parecidos com a pergunta e entrega ao LLM junto com ela) e passa a
conversa para uma pessoa (handoff) quando o cliente pede ou quando a IA não sabe responder.

A base que vem no repositório é **fictícia**: o FAQ de uma loja inventada ("Loja Exemplo"),
com 25 parágrafos. Nenhum dado real.

Legenda: ✅ provado (teste ou execução registrada aqui) · 🔶 hipótese (não testado) · ❌ não feito.

## Arquitetura

```
WhatsApp ──► Twilio ──► Flask  POST /whatsapp/message
                         │  1. valida a assinatura da Twilio (X-Twilio-Signature)
                         │  2. lê a sessão do usuário no Redis (histórico + "está em handoff?")
                         │
                         ├─ já em handoff ...........► encaminha a mensagem ao Slack, não responde
                         ├─ pediu "atendente" etc. ..► liga o handoff e avisa o Slack
                         └─ caso normal:
                              RAG: embedding da pergunta (sentence-transformers all-MiniLM-L6-v2)
                                   → 3 parágrafos mais próximos no índice FAISS
                              → gpt-4o-mini (OpenAI) com contexto + histórico
                              → se a IA responder "handoff", liga o handoff e avisa o Slack
                         │
                         └─► salva a sessão no Redis (24 h, últimas 10 trocas) e responde em TwiML
```

| Arquivo | Papel |
|---|---|
| `app.py` | cria o app Flask e registra a rota |
| `routes/whatsapp_routes.py` | webhook da Twilio, regras de handoff |
| `utils/rag_utils.py` | carrega `knowledge_base/documentos.md`, divide por parágrafo, cria o índice FAISS, busca |
| `utils/openai_utils.py` | monta o prompt e chama o gpt-4o-mini |
| `utils/redis_utils.py` | sessão do usuário no Redis |
| `utils/slack_utils.py` | avisos de handoff no Slack |
| `utils/email_utils.py` | envio de e-mail por SMTP — **existe e está testado, mas a rota não o chama**: hoje o handoff vai só para o Slack |
| `avaliacao/` | perguntas de avaliação e o script que mede a busca |

## Como rodar

Testado com Python 3.11.18 no Windows 11.

```bash
python -m venv .venv
source .venv/bin/activate        # no Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
```

Na primeira execução o modelo all-MiniLM-L6-v2 é baixado do Hugging Face (precisa de internet).

Para subir o bot, copie `.env.example` para `.env`, preencha as chaves e rode:

```bash
python app.py
```

O servidor sobe na porta 5000. Na Twilio, o webhook de mensagens recebidas aponta para
`https://<seu-endereço-público>/whatsapp/message`.

O que foi provado ao subir o servidor localmente (Flask real, requisições HTTP de verdade, token
da Twilio falso, **sem** Redis rodando e **sem** chave da OpenAI):

- ✅ `GET /` responde "Servidor do Chatbot está no ar!".
- ✅ POST com assinatura errada → 403.
- ✅ POST com assinatura certa → 200 com TwiML. Como não havia Redis nem chave, o bot registrou
  os dois erros no log e respondeu a mensagem amigável ("Desculpe, não consegui processar…"),
  sem quebrar.

## Testes

```bash
pytest
```

✅ **39 testes passam.** Eles foram escritos antes das correções e, contra o código original,
davam **14 falhas e 4 erros** (erros de sintaxe, índice FAISS que não era criado, busca que
quebrava, `choices.message` no lugar de `choices[0]`, base vazia e no caminho errado, e-mail sem
assunto e destinatário).

Nenhum teste usa serviço externo: OpenAI, Twilio (validação da assinatura), Redis, Slack e SMTP
são substituídos por versões falsas. O que usa o modelo de verdade é a parte de RAG (embeddings
e FAISS).

| Arquivo | O que cobre |
|---|---|
| `tests/test_importa.py` | todos os módulos importam; o app sobe; o cliente da OpenAI é criado (pega a incompatibilidade do `openai 1.35.3` com o `httpx 0.28`) |
| `tests/test_rag.py` | base carregada (15 a 30 parágrafos, de qualquer pasta, marcada como fictícia); índice FAISS com dimensão 384; busca devolve parágrafos da base; `top_k` maior que a base não repete parágrafo |
| `tests/test_openai.py` | `gerar_resposta` monta o prompt com o contexto do RAG e o histórico e usa o gpt-4o-mini (OpenAI falso, sem chave) |
| `tests/test_rotas.py` | a rota responde TwiML; histórico; gatilho de atendente; handoff ativo; IA pedindo handoff; assinatura inválida (403); GET (405); mensagem sem texto |
| `tests/test_integracoes.py` | sessão no Redis (padrão, salvar/ler, Redis fora do ar, corte do histórico); e-mail com cabeçalhos; Slack |
| `tests/test_avaliacao.py` | o conjunto de perguntas é válido e o script de avaliação roda |

## Avaliação da busca

```bash
python -m avaliacao.avaliar_busca
```

São 25 perguntas escritas como um cliente escreveria, cada uma com o parágrafo que deveria
ser encontrado (`avaliacao/perguntas.json`). O script usa a mesma função de busca do bot e conta
quantas vezes o parágrafo certo aparece entre os 3 primeiros (hit rate top-3).

✅ Resultado (rodado duas vezes, mesma saída):

| Métrica | Resultado |
|---|---|
| Hit rate top-3 | **80% (20 de 25)** |
| Hit rate top-1 | 64% (16 de 25) |

As 5 perguntas que erraram (o script lista cada uma):

- "Até que horas posso chamar no WhatsApp?" → esperado *Horário de atendimento*
- "Dá para dividir em 10 vezes?" → esperado *Parcelamento*
- "Quanto tempo demora para chegar no Nordeste?" → esperado *Prazo de entrega*
- "Como acompanho meu pedido?" → esperado *Rastreamento*
- "A panela chegou quebrada, o que eu faço?" → esperado *Produto com defeito*

**Isso mede só a busca, não a qualidade da resposta do LLM.** Um acerto aqui quer dizer que o
parágrafo certo chegou ao prompt; não quer dizer que o gpt-4o-mini respondeu bem.

## Limitações

- ❌ **Nenhum teste com as APIs reais.** OpenAI, Twilio (envio pelo WhatsApp), Redis, Slack e SMTP
  só foram exercitados com versões falsas.
- ❌ Docker e Gunicorn não foram executados (o Gunicorn não roda no Windows). O `Dockerfile`
  tinha erros de sintaxe nos `COPY`, que foram corrigidos, mas o build não foi testado.
- **Base fictícia e pequena** (25 parágrafos). O número da avaliação vale para esta base.
- **As perguntas de avaliação foram escritas pelo mesmo autor da base**, o que tende a deixar o
  número otimista. Cada parágrafo começa com o nome do tema ("Boleto: …"), o que também ajuda a
  busca.
- **Divisão por parágrafo** (linha em branco). Um parágrafo longo com vários assuntos vira um
  trecho só.
- 🔶 O all-MiniLM-L6-v2 foi treinado principalmente em inglês; é provável que parte dos erros da
  avaliação venha daí. Não testei outro modelo.
- A IA só aciona o handoff se responder exatamente a palavra "handoff" (maiúscula ou minúscula).
  Uma resposta como "Handoff." (com ponto) não é reconhecida. 🔶 Se o gpt-4o-mini responde assim
  na prática, não foi testado.
- 🔶 A validação da Twilio usa a URL que o Flask recebe. Atrás de um proxy que troca https por
  http, a assinatura pode não bater. Não testado.
- O modelo de embeddings e o índice são criados quando o módulo é importado; a primeira subida
  demora alguns segundos.

## O que foi corrigido

- `routes/whatsapp_routes.py`: `methods=)` → `methods=["POST"]`; `sessao.get("historico", )` →
  `[]`; mensagem sem `Body` não quebra mais.
- `utils/rag_utils.py`: `shape` → `shape[1]`; busca usa `indices[0]` e ignora o `-1` do FAISS;
  caminho `knowledge_base/` a partir da raiz do projeto (a pasta se chamava `knowledge_edge/`).
- `utils/openai_utils.py`: `choices.message` → `choices[0].message`.
- `utils/redis_utils.py`: dois erros de sintaxe (`"historico":,` e `= ` sem valor).
- `utils/email_utils.py`: assunto e destinatário sobrescreviam a mensagem inteira.
- `requirements.txt`: `httpx==0.27.2` fixado (o `openai 1.35.3` não cria o cliente com o
  `httpx 0.28`).
- `knowledge_base/documentos.md`: estava vazio; agora tem o FAQ fictício.
- `utils.py` da raiz removido: nada o importava, e o pacote `utils/` tem o mesmo nome.
