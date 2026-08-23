def replace_in_file(file_path, old, new):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    if old in content:
        content = content.replace(old, new)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Fixed {file_path}')
    else:
        print(f'Failed {file_path}')

replace_in_file(r'f:\supremeai\backend\memory\supabase_store.py', '        except Exception as e:\n        logger.debug(f"Error: {e}")', '        except Exception as e:\n            logger.debug(f"Error: {e}")')
replace_in_file(r'f:\supremeai\backend\services\intelligent_cache.py', '            except Exception as e:\n            logger.debug(f"Error: {e}")', '            except Exception as e:\n                logger.debug(f"Error: {e}")')
replace_in_file(r'f:\supremeai\backend\core\intelligent_cache.py', '            except Exception as e:\n            logger.debug(f"Error: {e}")', '            except Exception as e:\n                logger.debug(f"Error: {e}")')
replace_in_file(r'f:\supremeai\backend\scripts\superai_free_tier_monitor.py', '            except Exception as e:\n            logger.debug(f"Error: {e}")', '            except Exception as e:\n                logger.debug(f"Error: {e}")')
replace_in_file(r'f:\supremeai\backend\core\health\proactive_healer.py', '                except Exception as e:\n            logger.debug(f"Error: {e}")', '                except Exception as e:\n                    logger.debug(f"Error: {e}")')
replace_in_file(r'f:\supremeai\backend\services\security_auditor.py', "self.stats['by_severity] = self._count_by_severity(all_vulns)", "self.stats['by_severity'] = self._count_by_severity(all_vulns)")
replace_in_file(r'f:\supremeai\backend\core\competitive_kit.py', '        except Exception as e:\n            return VerifiedCitation(', '        except Exception as e:\n            logger.debug(f"Error: {e}")\n            return VerifiedCitation(')
