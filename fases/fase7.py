import re
from pathlib import Path

p = Path("app_relatorio.py")
s = p.read_text(encoding="utf-8")

def sub(old, new):
    global s
    assert s.count(old) == 1, "trecho nao encontrado (ou repetido): " + old[:70]
    s = s.replace(old, new)

def sub_re(padrao, novo, esperado):
    global s
    s, n = re.subn(padrao, novo, s)
    assert n == esperado, f"{padrao[:40]}: {n} ocorrencias (esperado {esperado})"

# 1) use_container_width (descontinuado) -> width
sub_re(r"use_container_width=True", 'width="stretch"', 22)
sub_re(r"use_container_width=False", 'width="content"', 1)

# 2) excecoes silenciosas passam a deixar rastro no log
sub("import hashlib\n", "import hashlib\nimport logging\n")
sub("from openpyxl.utils import get_column_letter\n", 'from openpyxl.utils import get_column_letter\n\n_log = logging.getLogger("gircp")\n')
sub('''                registrar_auditoria("erro_scan_malware", detalhe=f"{file_path}: {exc}")
            except Exception:
                pass''', '''                registrar_auditoria("erro_scan_malware", detalhe=f"{file_path}: {exc}")
            except Exception:
                _log.warning("falha ao registrar erro_scan_malware na auditoria", exc_info=True)''')
sub('''        registrar_auditoria(acao, detalhe=detalhe)
    except Exception:
        pass''', '''        registrar_auditoria(acao, detalhe=detalhe)
    except Exception:
        _log.warning("falha ao auditar %s", acao, exc_info=True)''')
sub('''            registrar_auditoria("integridade_codigo_violada", detalhe=f"hash_atual={atual[:16]}")
        except Exception:
            pass''', '''            registrar_auditoria("integridade_codigo_violada", detalhe=f"hash_atual={atual[:16]}")
        except Exception:
            _log.warning("falha ao registrar integridade_codigo_violada", exc_info=True)''')
sub('''            return _GEO_CACHE[chave]
    except Exception:
        pass''', '''            return _GEO_CACHE[chave]
    except Exception as exc:
        _log.info("geocodificacao falhou: %s", type(exc).__name__)''')
p.write_text(s, encoding="utf-8")

print("OK: Fase 7 (somente codigo) aplicada em", p)
