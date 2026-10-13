# ISNP — site institucional

Site estático do Instituto de Saúde do Norte do Pará, uma instituição do Grupo Norte.

Domínio oficial: https://www.institutodesaudedonortedopara.com/

## Publicação

GitHub Pages, branch `main`, diretório raiz (`/`). `.nojekyll` mantém a publicação estática e `CNAME` define o domínio oficial. O repositório está na organização `josuerosa-enterprise`, em `isnp-site`.

## Identidade e conteúdo

A composição editorial acompanha o Grupo Norte: títulos amplos, tipografia Inter, seções numeradas, linhas finas, botões retangulares e contraste entre áreas claras e escuras. A paleta vem da própria logo do ISNP: verde `#075437`, verde profundo `#073c2c` e verde `#247443`, com neutros e um verde claro de apoio.

- `index.html`: instituto, gestão médica, atuação, notícias e contato.
- `noticias/*.html`: quatro notícias, com conteúdo, títulos, descrições, dados estruturados, datas e URLs preservados.
- `styles.css` e `news.css`: estilos compartilhados, leitura editorial e adaptações para celular.
- `app.js`: navegação, diálogos e revisão de propostas.
- `isnp-logo.png`: logo original, apresentada por enquadramento CSS, sem alteração do arquivo.
- `cuidado-isnp.webp`: imagem ilustrativa existente, usada na abertura em telas maiores.
- `assets/fonts/inter-latin.woff2`: Inter local; licença SIL Open Font License em `assets/fonts/OFL.txt`.
- `robots.txt` e `sitemap.xml`: indexação e URLs canônicas.

As informações sobre contratos e contatos foram fornecidas pelo instituto. A revisão visual não atualiza o estado dos contratos nem altera os fatos das notícias. O formulário prepara a mensagem no navegador; o visitante conclui o envio pelo WhatsApp ou e-mail. Não há envio automático nem armazenamento permanente dos dados do formulário.

## Validações reproduzíveis

Requer Python 3.12+ e Node.js 22+. Executar na raiz do repositório:

```bash
python3 scripts/check_site.py
node --check app.js
node --test scripts/test_app.cjs
git diff --check
```

O primeiro comando verifica estrutura HTML, âncoras, recursos locais, navegação, alternativas textuais, identificação dos campos, metadados, dados estruturados, sitemap, indexabilidade declarada, contraste de cores e orçamento de recursos. Compara as notícias com o commit anterior à revisão `e25d4f90ed704017e9a7ad603b032a8efbbff453`; use um clone com esse histórico disponível.

O teste JavaScript verifica menu, retorno de foco ao fechar a proposta, campos e codificação das mensagens, revisão/edição, cópia com alternativa manual e visibilidade do contato flutuante. Usa um DOM simulado, sem enviar mensagens.

Para conferir a sintaxe de CSS com uma dependência isolada, usada apenas na validação:

```bash
python3 -m pip install --target /tmp/isnp-css-qa tinycss2==1.4.0
PYTHONPATH=/tmp/isnp-css-qa python3 scripts/check_styles.py
```

Após a publicação, com acesso à internet:

```bash
python3 scripts/check_live.py
```

Esse comando exige HTTP 200 e igualdade de conteúdo entre o checkout e as cinco páginas, dois CSS, JavaScript, fonte, sitemap e robots publicados. Também confere ausência de cabeçalho `noindex` e HTTP 404 para uma página inexistente.

## Limites de verificação

A revisão inclui layouts definidos para celular, tablet e desktop, `prefers-reduced-motion`, foco visível, navegação sem JavaScript e limites de recursos. Não houve navegador de QA disponível nesta execução. As verificações de código e HTTP não substituem uma inspeção visual, teste de teclado/leitor de tela em navegador, Lighthouse ou medições de Core Web Vitals. Nenhuma nota de desempenho ou posição no Google é prometida.
