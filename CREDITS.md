# Orbe — Edição Estúdio

**Orbe — Edição Estúdio**, versão `2.0.0`.

**Nexo Atelier** é o pseudônimo escolhido para a identidade e a personalização
do produto.

As alterações desta edição foram realizadas com assistência do Codex:

- logo com setas circulares azuis e brancas e ícones de instalação;
- confirmação compacta na instalação e funcionamento em segundo plano;
- entrada por arrastar e soltar e resumo da última ação;
- menu circular e janelas opacas em cinza escuro;
- interface em português, preferências e informações do produto;
- separação da inicialização, controle da aplicação, protocolo local, catálogo de ações e tarefas;
- divisão dos editores em módulos por ferramenta;
- namespace próprio para configurações, logs e comunicação local;
- testes de integração para as novas camadas e preservação dos arquivos de origem.

Os avisos de copyright e o texto de licença que acompanham o código permanecem
no arquivo `LICENSE`, incluído nas distribuições.

## Dependências

O aplicativo utiliza PySide6/Qt, Pillow, pillow-heif/libheif, PyMuPDF/MuPDF,
NumPy, python-docx e integrações específicas de plataforma. Cada dependência
mantém sua própria licença; os nomes e versões resolvidos ficam disponíveis por
`python -m pip list`. A licença MIT deste repositório não substitui essas licenças.

As fontes do Windows são lidas da instalação local para os testes visuais;
nenhuma fonte do sistema é distribuída com o código desta edição.
