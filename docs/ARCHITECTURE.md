# Arquitetura do Orbe

O pacote Python `orbe` reúne a aplicação, o menu circular e os editores.
O comando de execução é `python -m orbe`.

| Camada | Responsabilidade |
| --- | --- |
| `identity.py` | Nome, versão, pseudônimo e apresentação do produto |
| `application/bootstrap.py` | Ciclo de vida do processo e do Qt |
| `application/controller.py` | Conexão entre entrada de arquivos, telas e ações |
| `application/actions.py` | Seleção validada, catálogo de ferramentas e planos de conversão |
| `application/jobs.py` | Execução em segundo plano e entrega dos resultados à interface |
| `application/instance.py` | Recebimento de arquivos de uma segunda execução |
| `application/diagnostics.py` | Teste rápido de conversão, editores e fontes |
| `ui/theme.py` e `ui/shell.py` | Cores, estilos e estrutura das janelas |
| `ui/installation.py`, `ui/home.py`, `ui/preferences.py`, `ui/credits.py` | Confirmação de instalação e telas principais |
| `ui/orbit.py` | Geometria, pintura e eventos do menu circular |
| `ui/editors/` | Editor independente por ferramenta e componentes compartilhados |
| `convert.py`, `imaging.py`, `report.py` | Mecanismos de conversão e edição herdados |
| `preferences.py` | Persistência e inicialização com o sistema |
| `trigger.py`, `platform_*.py` | Integrações de teclado, mouse e sistema herdadas |

Fluxo: entrada de arquivos → seleção validada → catálogo de ações → tarefa em
segundo plano ou editor → resumo do resultado → notificação e atividade da sessão.

Os módulos `app.py`, `tools.py`, `window.py`, `settings.py` e `radial.py` são
fachadas de compatibilidade. O comportamento principal agora vive nas camadas
acima. O namespace de configurações é `NexoAtelier/Orbe`.
O nome dos arquivos finais continua protegido
contra sobrescrita e o arrastar e soltar sempre usa ação de cópia.

A primeira abertura mostra apenas `InstallationNotice` e grava a preferência
`welcomed`. As próximas inicializações ficam na bandeja. O instalador passa
`--installed` para exibir essa confirmação também após uma reinstalação ou quando
o processo já está ativo; a comunicação local trata esse pedido separadamente
da abertura manual da central. `--quiet` não mostra janelas nem consome o aviso.

## Verificação

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m orbe --selftest
```

Os testes cobrem conversão e ferramentas da base original, conversão combinada
de imagens para PDF, preservação dos originais, entrada por soltar arquivos,
seleção do menu, rejeição de ações incompatíveis, entrega no thread da interface,
apresentação do produto, acesso à licença e conexão completa entre menu e conversor.

O ambiente desta entrega foi Windows com Python 3.12. Os caminhos de macOS,
Linux e empacotamento não foram executados nesta máquina.

## Português do Brasil

`i18n.py` centraliza textos da interface, nomes de campos de metadados, pluralização
e sufixos dos resultados. As chaves internas das ações permanecem estáveis.
A inicialização carrega `qtbase_pt_BR.qm` do PySide6; `Orbe.spec` inclui esse catálogo
na compilação opcional. As convenções numéricas usam vírgula decimal.

## Superfícies opacas

`ui/surfaces.py` desenha os fundos sólidos das janelas, do menu radial e das
notificações. Os componentes ativos da interface não capturam a tela nem usam
desfoque ou refração. As rotinas gráficas originais permanecem no código de origem
para compatibilidade e atribuição, sem participar da pintura destas superfícies.
