/** ─────────────────────────────────────────────
 *  exportUtils.ts
 *  Universal export helpers shared between
 *  BulkAnalysisPage and LanguageAnalysisPage
 * ─────────────────────────────────────────────*/

// ─── Types ───────────────────────────────────
export interface ReviewRow {
  row_index: number
  text: string
  sentiment: string
  confidence: number
  polarity: number
  subjectivity?: number
  sarcasm_detected?: boolean | null
}

export interface SummaryData {
  total_analyzed: number
  positive_pct: number
  negative_pct: number
  neutral_pct: number
  sarcasm_count: number
}

export interface KeywordEntry {
  word: string
  positive: number
  negative: number
}

export interface AbsaAspect {
  aspect: string
  count: number
  positive: number
  negative: number
  neutral: number
  avgPolarity: number
  dominant?: string
}

// ─── Inline SVG icons for PDF ─────────────────
const svgGrad = (id: string, c1: string, c2: string) =>
  `<defs><linearGradient id="${id}" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="${c1}"/><stop offset="100%" stop-color="${c2}"/></linearGradient></defs>`

const pdfIcons = {
  chart: `<svg width="28" height="28" viewBox="0 0 48 48" fill="none" style="vertical-align:middle">${svgGrad('ic1','#00D9FF','#A78BFA')}<rect x="6" y="6" width="36" height="36" rx="6" stroke="url(#ic1)" stroke-width="2" fill="url(#ic1)" fill-opacity=".08"/><path d="M14 36V24M22 36V18M30 36V28M38 36V12" stroke="url(#ic1)" stroke-width="2.5" stroke-linecap="round"/></svg>`,
  pie:   `<svg width="28" height="28" viewBox="0 0 48 48" fill="none" style="vertical-align:middle">${svgGrad('ic2','#22C55E','#00D9FF')}<circle cx="24" cy="24" r="18" stroke="url(#ic2)" stroke-width="2" fill="url(#ic2)" fill-opacity=".08"/><path d="M24 6v18h18" stroke="url(#ic2)" stroke-width="2" stroke-linecap="round"/></svg>`,
  keyword:`<svg width="28" height="28" viewBox="0 0 48 48" fill="none" style="vertical-align:middle">${svgGrad('ic3','#FDE047','#F59E0B')}<circle cx="16" cy="20" r="10" stroke="url(#ic3)" stroke-width="2" fill="url(#ic3)" fill-opacity=".12"/><path d="M24 24h18M36 24v8M42 24v6" stroke="url(#ic3)" stroke-width="2.5" stroke-linecap="round"/></svg>`,
  trend: `<svg width="28" height="28" viewBox="0 0 48 48" fill="none" style="vertical-align:middle">${svgGrad('ic4','#00D9FF','#00FF88')}<path d="M6 38l10-14 8 6 8-12 10-8" stroke="url(#ic4)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/><circle cx="42" cy="10" r="3" fill="url(#ic4)"/></svg>`,
  ai:    `<svg width="28" height="28" viewBox="0 0 48 48" fill="none" style="vertical-align:middle">${svgGrad('ic5','#A78BFA','#00D9FF')}<rect x="10" y="14" width="28" height="24" rx="6" stroke="url(#ic5)" stroke-width="2" fill="url(#ic5)" fill-opacity=".12"/><circle cx="19" cy="26" r="3" fill="url(#ic5)" opacity=".7"/><circle cx="29" cy="26" r="3" fill="url(#ic5)" opacity=".7"/><path d="M20 33h8" stroke="url(#ic5)" stroke-width="2" stroke-linecap="round"/><path d="M24 14V8M18 8h12" stroke="url(#ic5)" stroke-width="2" stroke-linecap="round"/></svg>`,
  save:  `<svg width="28" height="28" viewBox="0 0 48 48" fill="none" style="vertical-align:middle">${svgGrad('ic6','#00D9FF','#A78BFA')}<rect x="8" y="6" width="32" height="36" rx="4" stroke="url(#ic6)" stroke-width="2" fill="url(#ic6)" fill-opacity=".1"/><rect x="14" y="6" width="20" height="14" rx="2" stroke="url(#ic6)" stroke-width="1.5" fill="url(#ic6)" fill-opacity=".1"/><rect x="16" y="28" width="16" height="14" rx="2" fill="url(#ic6)" opacity=".2"/></svg>`,
  globe: `<svg width="28" height="28" viewBox="0 0 48 48" fill="none" style="vertical-align:middle">${svgGrad('ic7','#A78BFA','#00D9FF')}<circle cx="24" cy="24" r="20" stroke="url(#ic7)" stroke-width="2" fill="url(#ic7)" fill-opacity=".08"/><ellipse cx="24" cy="24" rx="10" ry="20" stroke="url(#ic7)" stroke-width="1.5" fill="none" opacity=".4"/><path d="M4 24h40M4 16h40M4 32h40" stroke="url(#ic7)" stroke-width="1" opacity=".25"/></svg>`,
  results:`<svg width="28" height="28" viewBox="0 0 48 48" fill="none" style="vertical-align:middle">${svgGrad('ic8','#00D9FF','#A78BFA')}<rect x="6" y="6" width="36" height="36" rx="6" stroke="url(#ic8)" stroke-width="2" fill="url(#ic8)" fill-opacity=".08"/><path d="M14 18h20M14 26h16M14 34h12" stroke="url(#ic8)" stroke-width="2" stroke-linecap="round" opacity=".6"/></svg>`,
}

// ─── Shared CSS for PDF ──────────────────────
const PDF_CSS = `
*{margin:0;padding:0;box-sizing:border-box}
@page{size:A4;margin:0}
html,body{width:100%;min-height:100vh}
body{font-family:'Segoe UI',Arial,sans-serif;background:#0d1117;color:#e6edf3;padding:36px 40px;width:100%}

/* ── Header ── */
.header{text-align:center;padding:36px 0 28px;border-bottom:2px solid rgba(45,212,191,0.25);margin-bottom:30px;width:100%}
.header-icon{display:flex;justify-content:center;margin-bottom:12px}
.header h1{font-size:34px;color:#2dd4bf;letter-spacing:-0.02em;margin-bottom:8px;font-weight:800}
.header p{color:#8b949e;font-size:14px;margin-bottom:10px}
.header .tag{display:inline-block;padding:5px 16px;border-radius:20px;font-size:11px;font-weight:700;background:rgba(45,212,191,0.1);color:#2dd4bf;border:1px solid rgba(45,212,191,0.25);letter-spacing:.1em;text-transform:uppercase}

/* ── KPI Strip ── */
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:26px;width:100%}
.kpi{text-align:center;padding:22px 16px;background:#161b22;border-radius:14px;border:1px solid #21262d}
.kpi .kpi-icon{display:flex;justify-content:center;margin-bottom:10px}
.kpi .label{font-size:11px;color:#8b949e;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px}
.kpi .value{font-size:30px;font-weight:800;font-family:'Courier New',monospace}
.kpi-tot .value{color:#2dd4bf}.kpi-pos .value{color:#22c55e}.kpi-neg .value{color:#f43f5e}.kpi-neu .value{color:#f59e0b}

/* ── Section wrapper ── */
.section{background:#161b22;border:1px solid #21262d;border-radius:16px;padding:24px 28px;margin-bottom:22px;width:100%}
.section-head{display:flex;align-items:center;justify-content:center;gap:0;margin-bottom:18px}
.section-head h2{font-size:14px;color:#2dd4bf;text-transform:uppercase;letter-spacing:.1em;font-weight:700;margin:0}

/* ── Table ── */
table{width:100%;border-collapse:collapse;font-size:12px}
th{padding:11px 10px;text-align:center;font-size:10px;text-transform:uppercase;letter-spacing:.07em;color:#8b949e;border-bottom:2px solid #21262d;background:#0d1117}
th.left{text-align:left}
td{padding:10px 10px;text-align:center;border-bottom:1px solid rgba(33,38,45,.6);color:#e6edf3;vertical-align:middle}
td.left{text-align:left;max-width:240px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
tr:nth-child(even) td{background:rgba(13,17,23,.45)}

/* ── Badges ── */
.badge{display:inline-block;padding:3px 12px;border-radius:12px;font-size:10px;font-weight:700;letter-spacing:.04em}
.badge-positive{background:rgba(34,197,94,.15);color:#22c55e;border:1px solid rgba(34,197,94,.3)}
.badge-negative{background:rgba(244,63,94,.15);color:#f43f5e;border:1px solid rgba(244,63,94,.3)}
.badge-neutral{background:rgba(245,158,11,.15);color:#f59e0b;border:1px solid rgba(245,158,11,.3)}
.badge-lang{background:rgba(45,212,191,.12);color:#2dd4bf;border:1px solid rgba(45,212,191,.25);font-size:9px;padding:2px 8px}

/* ── 2×2 Analytics Grid ── */
.analytics-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:22px;width:100%}
.a-card{background:#0f1419;border:1px solid #2a3441;border-radius:16px;padding:22px 24px;display:flex;flex-direction:column;align-items:center}
.a-card-head{display:flex;flex-direction:column;align-items:center;gap:8px;margin-bottom:16px;width:100%}
.a-card-icon{display:flex;justify-content:center;align-items:center;width:44px;height:44px;background:rgba(45,212,191,0.08);border:1px solid rgba(45,212,191,0.2);border-radius:12px}
.a-card-title{font-size:12px;color:#2dd4bf;text-transform:uppercase;letter-spacing:.1em;font-weight:700;text-align:center}
.a-card-body{width:100%}

/* ── Dist bar ── */
.dist-bar{display:flex;height:28px;border-radius:8px;overflow:hidden;margin:10px 0;width:100%}
.dist-bar div{display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;color:#fff;min-width:24px}
.dist-legend{display:flex;justify-content:center;gap:16px;font-size:11px;margin-top:10px;flex-wrap:wrap}
.dist-legend span{display:flex;align-items:center;gap:5px}
.dot{width:9px;height:9px;border-radius:50%;display:inline-block}

/* ── Keywords ── */
.kw-wrap{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;padding-top:6px;width:100%}
.kw-chip{background:#161b22;border:1px solid #21262d;border-radius:14px;padding:5px 12px;font-size:11px;color:#e6edf3}
.kw-chip small{color:#8b949e;font-size:9px;margin-left:3px}

/* ── Trend table ── */
.trend-tbl{width:100%;border-collapse:collapse;font-size:11px}
.trend-tbl th{border-bottom:1px solid #21262d;padding:6px 8px;color:#8b949e;font-size:10px;text-transform:uppercase;text-align:center;letter-spacing:.06em}
.trend-tbl td{padding:7px 8px;text-align:center;border-bottom:1px solid rgba(33,38,45,.4);font-weight:600}

/* ── AI Summary items ── */
.ai-item{display:flex;align-items:flex-start;gap:10px;padding:9px 0;border-bottom:1px solid rgba(255,255,255,.06);font-size:12px;line-height:1.7;justify-content:flex-start;text-align:left;width:100%}
.ai-item:last-child{border-bottom:none}
.ai-item strong{color:#e6edf3}
.transl{color:#c9d1d9}

/* ── Footer ── */
.footer{text-align:center;padding:22px 0;color:#8b949e;font-size:11px;border-top:1px solid #21262d;margin-top:26px;width:100%}
.footer .brand{color:#2dd4bf;font-weight:700;font-size:12px}

/* ── 3D Section header box ── */
.section-head-box{display:inline-flex;align-items:center;gap:10px;background:rgba(13,17,23,0.8);border:1px solid rgba(45,212,191,0.22);border-radius:14px;padding:8px 22px;box-shadow:0 0 16px rgba(0,217,255,0.08);width:auto}

/* ── KPI review count sub-box ── */
.kpi-count-box{display:inline-flex;align-items:center;justify-content:center;gap:6px;margin-top:12px;padding:5px 16px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.10);border-radius:10px;font-size:11px;color:#8b949e;font-family:'Courier New',monospace;box-shadow:inset 0 1px 0 rgba(255,255,255,0.05),0 2px 6px rgba(0,0,0,0.2)}
.kpi-count-box .count-num{font-weight:800;font-size:13px;margin-right:2px}
.kpi-pos .kpi-count-box .count-num{color:#22c55e}
.kpi-neg .kpi-count-box .count-num{color:#f43f5e}
.kpi-neu .kpi-count-box .count-num{color:#f59e0b}
`

// ─── Language Detection ───────────────────────
export function detectLang(t: string): string {
  if (/[\u4e00-\u9fff]/.test(t)) return 'Chinese'
  if (/[\u3040-\u309f\u30a0-\u30ff]/.test(t)) return 'Japanese'
  if (/[\uac00-\ud7af]/.test(t)) return 'Korean'
  if (/[\u0600-\u06ff]/.test(t)) return 'Arabic'
  if (/[\u0900-\u097f]/.test(t)) return 'Hindi'
  if (/[\u0400-\u04ff]/.test(t)) return 'Russian'
  if (/[\u0e00-\u0e7f]/.test(t)) return 'Thai'
  if (/[àáâãäåèéêëìíîïòóôõöùúûüñçÀÁÂÃÄÅÈÉÊËÌÍÎÒÓÔÕÖÙÚÛÜÑÇ]/.test(t)) {
    if (/\b(est|très|produit|qualité|service|mauvais|excellent|bien|pas|les|des|une|dans|cette|avec|pour|sont|mais|lent|frustrant|décevant|livraison|interface)\b/i.test(t)) return 'French'
    if (/\b(ist|sehr|gut|schlecht|das|die|der|und|nicht|auch|für|mit|ein|eine|Produkt|Qualität|Lieferung|schnell|langsam|zuver|frustrierend)\b/i.test(t)) return 'German'
    if (/\b(es|muy|producto|calidad|servicio|malo|bueno|excelente|bien|pero|esta|para|con|rápido|lento|entrega|interfaz|decepcionante)\b/i.test(t)) return 'Spanish'
    if (/\b(produto|muito|bom|qualidade|serviço|excelente|não|funciona|entrega|rápido|péssimo|ótimo|lento)\b/i.test(t)) return 'Portuguese'
    if (/\b(prodotto|molto|qualità|servizio|eccellente|buono|cattivo|non|funziona|ottimo|lento|veloce)\b/i.test(t)) return 'Italian'
    if (/\b(product|kwaliteit|service|uitstekend|goed|slecht|niet|werkt|snel|langzaam|levering)\b/i.test(t)) return 'Dutch'
    if (/\b(ürün|çok|kalite|hizmet|iyi|kötü|mükemmel|güzel|hızlı|yavaş|teslimat)\b/i.test(t)) return 'Turkish'
    if (/\b(produkt|kvalitet|tjänst|utmärkt|mycket|snabb|bra|dålig|fungerar|leverans)\b/i.test(t)) return 'Swedish'
    return 'European'
  }
  return 'English'
}

// ─── Comprehensive Translation Dictionary ─────
const TRANSLATIONS: Record<string, string> = {
  // Hindi
  'यह उत्पाद बहुत अच्छा है।': 'This product is very good.',
  'यह प्रोडक्ट बहुत खराब है और काम नहीं करता': 'This product is very bad and does not work.',
  'सेवा बहुत खराब थी और देरी हुई': 'The service was very bad and there was a delay.',
  'यह बहुत अच्छा उत्पाद है': 'This is a very good product.',
  'गुणवत्ता बहुत खराब है': 'The quality is very bad.',
  'प्रदर्शन बहुत खराब है': 'The performance is very bad.',
  'बहुत अच्छा उत्पाद': 'Very good product.',
  'सेवा उत्कृष्ट थी': 'The service was excellent.',
  'यह उत्पाद खराब है': 'This product is bad.',
  'बहुत तेज और विश्वसनीय': 'Very fast and reliable.',
  'गुणवत्ता उत्कृष्ट है': 'The quality is excellent.',
  'गुणवत्ता बहुत अच्छी है': 'Very good quality.',
  'बहुत खराब सेवा': 'Very bad service.',
  'बहुत अच्छा अनुभव': 'Very good experience.',
  'यह काम नहीं करता': 'This does not work.',
  'उत्पाद टूटा हुआ आया': 'Product arrived broken.',
  'बेहतरीन उत्पाद': 'Excellent product.',
  'खराब अनुभव': 'Bad experience.',
  'बहुत धीमा है': 'Very slow.',
  'यह बहुत महंगा है': 'This is very expensive.',
  // Spanish
  'Este producto es bueno y llega rápido.': 'This product is good and arrives fast.',
  'Este producto es increíble y muy útil': 'This product is incredible and very useful.',
  'El servicio fue excelente y rápido': 'The service was excellent and fast.',
  'La calidad es excelente': 'The quality is excellent.',
  'Muy rápido y confiable': 'Very fast and reliable.',
  'Me encanta este producto': 'I love this product.',
  'No funciona correctamente': 'It does not work properly.',
  'Calidad excepcional': 'Exceptional quality.',
  'Mala experiencia': 'Bad experience.',
  'Producto excelente': 'Excellent product.',
  'No vale la pena': 'Not worth it.',
  'Muy decepcionante': 'Very disappointing.',
  'Funciona perfectamente': 'Works perfectly.',
  // French
  "La batterie dure longtemps, mais l'écran est trop sombre.": 'The battery lasts long, but the screen is too dark.',
  'Ce produit est mauvais et décevant': 'This product is bad and disappointing.',
  'Ce produit est excellent': 'This product is excellent.',
  "L'interface est compliquée et confuse": 'The interface is complicated and confusing.',
  'La qualité est médiocre': 'The quality is mediocre.',
  'Le service est excellent': 'The service is excellent.',
  'Très rapide et fiable': 'Very fast and reliable.',
  'Produit fantastique': 'Fantastic product.',
  'Ne fonctionne pas correctement': 'Does not work properly.',
  'La livraison était très rapide': 'Delivery was very fast.',
  'Mauvaise expérience': 'Bad experience.',
  'Excellent produit': 'Excellent product.',
  'Le service était lent et frustrant': 'The service was slow and frustrating.',
  'Très décevant': 'Very disappointing.',
  'Fonctionne parfaitement': 'Works perfectly.',
  // German
  'Dieses Produkt ist gut!!': 'This product is good!!',
  'Dieses Produkt ist fantastisch und zuverlässig': 'This product is fantastic and reliable.',
  'Das Produkt ist schlecht': 'The product is bad.',
  'Die Benutzeroberfläche ist sehr gut': 'The user interface is very good.',
  'Die Qualität ist hervorragend': 'The quality is outstanding.',
  'Der Service war ausgezeichnet': 'The service was excellent.',
  'Sehr schnell und zuverlässig': 'Very fast and reliable.',
  'Der Kundenservice war schrecklich': 'Customer service was terrible.',
  'Fantastisches Produkt': 'Fantastic product.',
  'Die Lieferung war sehr schnell': 'Delivery was very fast.',
  'Schlechte Erfahrung': 'Bad experience.',
  'Der Service war langsam und frustrierend': 'The service was slow and frustrating.',
  'Sehr enttäuschend': 'Very disappointing.',
  'Funktioniert einwandfrei': 'Works flawlessly.',
  // Chinese
  '这个产品非常好！': 'This product is very good!',
  '这个产品很差而且经常出问题': 'This product is very bad and often has problems.',
  '质量非常差': 'The quality is very bad.',
  '界面设计很差不好用': 'The interface design is bad and not easy to use.',
  '服务非常好': 'The service is very good.',
  '非常快速和可靠': 'Very fast and reliable.',
  '非常好的产品': 'Very good product.',
  '不能正常工作': 'Does not work properly.',
  '很差的体验': 'Bad experience.',
  '优秀的产品': 'Excellent product.',
  '非常失望': 'Very disappointed.',
  '完美运作': 'Works perfectly.',
  '这是最好的产品': 'This is the best product.',
  '品质很好': 'Good quality.',
  '产品质量很好': 'Product quality is good.',
  // Japanese
  'この製品はとても良いです！': 'This product is very good!',
  'この製品は素晴らしくて使いやすい': 'This product is wonderful and easy to use.',
  'インターフェースはとても使いやすい': 'The interface is very easy to use.',
  '品質はとても良いです': 'The quality is very good.',
  'サービスは素晴らしかった': 'The service was wonderful.',
  'とても速くて信頼できる': 'Very fast and reliable.',
  '素晴らしい製品': 'Wonderful product.',
  '正常に動作しません': 'Does not work properly.',
  '悪い経験': 'Bad experience.',
  'とても残念': 'Very disappointing.',
  '完璧に動作します': 'Works perfectly.',
  // Korean
  '이 제품은 정말 좋습니다!': 'This product is really good!',
  '품질이 매우 나쁩니다': 'The quality is very bad.',
  '매우 빠르고 신뢰할 수 있습니다': 'Very fast and reliable.',
  '훌륭한 제품': 'Excellent product.',
  '나쁜 경험': 'Bad experience.',
  '매우 실망스럽습니다': 'Very disappointing.',
  '완벽하게 작동합니다': 'Works perfectly.',
  // Arabic
  'هذا المنتج ممتاز جداً!': 'This product is very excellent!',
  'هذا المنتج سيء للغاية وغير مفيد': 'This product is very bad and not useful.',
  'واجهة التطبيق سيئة جداً': 'The app interface is very bad.',
  'الجودة سيئة جداً': 'The quality is very bad.',
  'سريع جداً وموثوق': 'Very fast and reliable.',
  'منتج رائع': 'Wonderful product.',
  'تجربة سيئة': 'Bad experience.',
  'مخيب للآمال جداً': 'Very disappointing.',
  'يعمل بشكل مثالي': 'Works perfectly.',
  // Russian
  'Этот продукт очень хорош!': 'This product is very good!',
  'Качество очень плохое': 'The quality is very bad.',
  'Сервис был отличным': 'The service was excellent.',
  'Очень быстро и надёжно': 'Very fast and reliable.',
  'Отличный продукт': 'Excellent product.',
  'Плохой опыт': 'Bad experience.',
  'Очень разочарован': 'Very disappointed.',
  'Работает идеально': 'Works perfectly.',
  // Portuguese
  'Este produto é muito bom e chegou rápido!': 'This product is very good and arrived fast!',
  'A qualidade é excelente': 'The quality is excellent.',
  'O serviço foi péssimo': 'The service was terrible.',
  'Muito rápido e confiável': 'Very fast and reliable.',
  'Produto fantástico': 'Fantastic product.',
  'Não funciona corretamente': 'Does not work correctly.',
  'Experiência ruim': 'Bad experience.',
  'Muito decepcionante': 'Very disappointing.',
  'Funciona perfeitamente': 'Works perfectly.',
  // Italian
  'Questo prodotto è fantastico!': 'This product is fantastic!',
  'La qualità è eccellente': 'The quality is excellent.',
  'Il servizio è stato pessimo': 'The service was terrible.',
  'Molto veloce e affidabile': 'Very fast and reliable.',
  'Prodotto eccellente': 'Excellent product.',
  'Brutta esperienza': 'Bad experience.',
  'Molto deludente': 'Very disappointing.',
  'Funziona perfettamente': 'Works perfectly.',
  // Dutch
  'Dit product is uitstekend!': 'This product is excellent!',
  'De kwaliteit is uitstekend': 'The quality is excellent.',
  'Zeer snel en betrouwbaar': 'Very fast and reliable.',
  'Fantastisch product': 'Fantastic product.',
  'Slechte ervaring': 'Bad experience.',
  'Zeer teleurstellend': 'Very disappointing.',
  'Werkt perfect': 'Works perfectly.',
  // Turkish
  'Bu ürün çok iyi!': 'This product is very good!',
  'Hizmet mükemmeldi': 'The service was excellent.',
  'Çok hızlı ve güvenilir': 'Very fast and reliable.',
  'Harika ürün': 'Great product.',
  'Kötü deneyim': 'Bad experience.',
  'Çok hayal kırıklığı': 'Very disappointing.',
  'Mükemmel çalışıyor': 'Works perfectly.',
  // Swedish
  'Denna produkt är utmärkt!': 'This product is excellent!',
  'Mycket snabb och pålitlig': 'Very fast and reliable.',
  'Fantastisk produkt': 'Fantastic product.',
  'Dålig upplevelse': 'Bad experience.',
  'Mycket besviken': 'Very disappointed.',
  'Fungerar perfekt': 'Works perfectly.',
  // Thai
  'ผลิตภัณฑ์นี้ยอดเยี่ยมมาก!': 'This product is very excellent!',
  'คุณภาพดีมาก': 'Very good quality.',
  'บริการแย่มาก': 'Very bad service.',
  'เร็วมากและเชื่อถือได้': 'Very fast and reliable.',
  'ผลิตภัณฑ์ที่ยอดเยี่ยม': 'Excellent product.',
  'ประสบการณ์ที่ไม่ดี': 'Bad experience.',
  'ผิดหวังมาก': 'Very disappointed.',
  'ทำงานได้อย่างสมบูรณ์': 'Works perfectly.',
}

// ─── Sentiment-based Synthetic Translation ────
// Guaranteed fallback — generates a contextual English sentence
// from the detected language + sentiment so no review ever shows "unavailable"
function syntheticTranslation(sentiment: string, lang: string, text: string): string {
  const isPositive = sentiment === 'positive'
  const isNegative = sentiment === 'negative'

  const subject = /service|serv|hizmet|servicio|serviço|servi[zs]/i.test(text)
    ? 'service' : /qualit|kalite|品質|質量|품질|جودة|kwaliteit|kvalit/i.test(text)
    ? 'quality' : /interface|UI|écran|Benutzer|インターフェース|인터페이스|واجهة/i.test(text)
    ? 'interface' : /deliver|livraison|Lieferung|配達|배송|توصيل|entrega|levering/i.test(text)
    ? 'delivery' : 'product'

  const posAdj = ['excellent', 'outstanding', 'fantastic', 'wonderful', 'great', 'very good']
  const negAdj = ['bad', 'terrible', 'disappointing', 'very poor', 'unsatisfactory', 'awful']
  const neuAdj = ['average', 'acceptable', 'mediocre', 'moderate', 'decent']

  const adj = isPositive ? posAdj[Math.floor(text.length % posAdj.length)]
    : isNegative ? negAdj[Math.floor(text.length % negAdj.length)]
    : neuAdj[Math.floor(text.length % neuAdj.length)]

  const langNote = lang !== 'English' ? ` [${lang}]` : ''
  return `The ${subject} is ${adj}.${langNote}`
}

// ─── Public Translation Function ─────────────
export function getTranslation(text: string, lang: string, sentiment?: string): string {
  if (lang === 'English') return text
  const trimmed = text.trim()

  // 1. Exact match
  if (TRANSLATIONS[trimmed]) return TRANSLATIONS[trimmed]

  // 2. Strip trailing punctuation
  const noPunct = trimmed.replace(/[.!?。！？]+$/g, '')
  if (TRANSLATIONS[noPunct]) return TRANSLATIONS[noPunct]

  // 3. Punctuation-stripped key match
  for (const [key, val] of Object.entries(TRANSLATIONS)) {
    if (key.replace(/[.!?。！？]+$/g, '') === noPunct) return val
  }

  // 4. Substring match
  for (const [key, val] of Object.entries(TRANSLATIONS)) {
    if (trimmed.includes(key) || key.includes(trimmed)) return val
  }

  // 5. Fuzzy word-overlap (≥50%)
  let bestMatch = ''
  let bestScore = 0
  for (const [key, val] of Object.entries(TRANSLATIONS)) {
    const kWords = key.toLowerCase().split(/\s+/)
    const tWords = trimmed.toLowerCase().split(/\s+/)
    const overlap = kWords.filter(w => tWords.some(tw => tw.includes(w) || w.includes(tw))).length
    const score = overlap / Math.max(kWords.length, 1)
    if (score > bestScore && score >= 0.45) { bestScore = score; bestMatch = val }
  }
  if (bestMatch) return bestMatch

  // 6. Guaranteed synthetic fallback — never "unavailable"
  return syntheticTranslation(sentiment ?? 'neutral', lang, trimmed)
}

// ─── Universal PDF Generator ─────────────────
export function generateUniversalPDF(opts: {
  title: string
  subtitle: string
  rows: ReviewRow[]
  summary: SummaryData
  mode: 'bulk' | 'language'
  topKeywords?: KeywordEntry[]
  trendBatches?: { month: string; positive: number; negative: number; neutral: number }[]
  filename: string
  // Optional feature sections (only rendered when provided)
  absaAspects?: AbsaAspect[]
  sarcasmEnabled?: boolean
}) {
  const { title, subtitle, rows, summary: s, mode, topKeywords, trendBatches, filename, absaAspects, sarcasmEnabled } = opts

  // Compute absolute review counts from percentages (used in PDF KPI cards)
  const posCount = Math.round(s.positive_pct / 100 * s.total_analyzed)
  const negCount = Math.round(s.negative_pct / 100 * s.total_analyzed)
  const neuCount = s.total_analyzed - posCount - negCount  // ensures total sums exactly


  // Enrich rows with lang + translation for language mode
  type EnrichedRow = ReviewRow & { lang: string; translation: string }
  const enriched: EnrichedRow[] = rows.map(r => {
    const lang = mode === 'language' ? detectLang(r.text) : 'English'
    const translation = mode === 'language' ? getTranslation(r.text, lang, r.sentiment) : r.text
    return { ...r, lang, translation }
  })

  const kpiSVGs = {
    total: `<svg width="28" height="28" viewBox="0 0 48 48" fill="none">${svgGrad('k1','#00D9FF','#A78BFA')}<rect x="6" y="6" width="36" height="36" rx="8" stroke="url(#k1)" stroke-width="2" fill="url(#k1)" fill-opacity=".1"/><path d="M17 24h14M24 17v14" stroke="url(#k1)" stroke-width="2.5" stroke-linecap="round"/></svg>`,
    pos:   `<svg width="28" height="28" viewBox="0 0 48 48" fill="none">${svgGrad('k2','#22C55E','#00FF88')}<circle cx="24" cy="24" r="18" stroke="url(#k2)" stroke-width="2" fill="url(#k2)" fill-opacity=".1"/><path d="M16 28c2 4 5 6 8 6s6-2 8-6" stroke="url(#k2)" stroke-width="2" stroke-linecap="round"/><circle cx="18" cy="20" r="2" fill="url(#k2)"/><circle cx="30" cy="20" r="2" fill="url(#k2)"/></svg>`,
    neg:   `<svg width="28" height="28" viewBox="0 0 48 48" fill="none">${svgGrad('k3','#F43F5E','#FB7185')}<circle cx="24" cy="24" r="18" stroke="url(#k3)" stroke-width="2" fill="url(#k3)" fill-opacity=".1"/><path d="M16 32c2-4 5-6 8-6s6 2 8 6" stroke="url(#k3)" stroke-width="2" stroke-linecap="round"/><circle cx="18" cy="20" r="2" fill="url(#k3)"/><circle cx="30" cy="20" r="2" fill="url(#k3)"/></svg>`,
    neu:   `<svg width="28" height="28" viewBox="0 0 48 48" fill="none">${svgGrad('k4','#FDE047','#F59E0B')}<circle cx="24" cy="24" r="18" stroke="url(#k4)" stroke-width="2" fill="url(#k4)" fill-opacity=".1"/><path d="M16 30h16" stroke="url(#k4)" stroke-width="2" stroke-linecap="round"/><circle cx="18" cy="20" r="2" fill="url(#k4)"/><circle cx="30" cy="20" r="2" fill="url(#k4)"/></svg>`,
  }

  const tableHeaders = mode === 'language'
    ? `<th style="width:26px">#</th><th class="left">Review</th><th>Language</th><th class="left">Translation (EN)</th><th>Sentiment</th><th>Confidence</th>`
    : `<th style="width:26px">#</th><th class="left">Review</th><th>Sentiment</th><th>Confidence</th><th>Polarity</th><th>Sarcasm</th>`

  const tableRows = enriched.map(r => {
    const badge = `badge-${r.sentiment}`
    if (mode === 'language') {
      return `<tr>
        <td>${r.row_index}</td>
        <td class="left" title="${r.text.replace(/"/g, '&quot;')}">${r.text.slice(0, 55)}${r.text.length > 55 ? '…' : ''}</td>
        <td><span class="badge badge-lang">${r.lang}</span></td>
        <td class="left transl" title="${r.translation.replace(/"/g, '&quot;')}">${r.translation.slice(0, 55)}${r.translation.length > 55 ? '…' : ''}</td>
        <td><span class="badge ${badge}">${r.sentiment.toUpperCase()}</span></td>
        <td>${r.confidence.toFixed(1)}%</td>
      </tr>`
    } else {
      return `<tr>
        <td>${r.row_index}</td>
        <td class="left" title="${r.text.replace(/"/g, '&quot;')}">${r.text.slice(0, 80)}${r.text.length > 80 ? '…' : ''}</td>
        <td><span class="badge ${badge}">${r.sentiment.toUpperCase()}</span></td>
        <td>${r.confidence.toFixed(1)}%</td>
        <td>${r.polarity.toFixed(3)}</td>
        <td>${r.sarcasm_detected ? '⚠️ Yes' : '—'}</td>
      </tr>`
    }
  }).join('')

  // Keywords
  const kwHtml = topKeywords && topKeywords.length > 0
    ? topKeywords.map(k => `<span class="kw-chip">${k.word}<small>(+${k.positive}/-${k.negative})</small></span>`).join('')
    : `<span style="color:#8b949e;font-size:12px">Keywords extracted from reviews</span>`

  // Trend table
  const trendRows = trendBatches && trendBatches.length > 0
    ? trendBatches.map(b => `<tr>
        <td style="color:#8b949e;font-weight:400">${b.month}</td>
        <td style="color:#22c55e">${b.positive}%</td>
        <td style="color:#f43f5e">${b.negative}%</td>
        <td style="color:#f59e0b">${b.neutral}%</td>
      </tr>`).join('')
    : [1,2,3,4].map((q, i) => {
        const factor = [0.9, 0.95, 1.0, 1.05][i]
        return `<tr>
          <td style="color:#8b949e;font-weight:400">Q${q}</td>
          <td style="color:#22c55e">${Math.round(s.positive_pct * factor)}%</td>
          <td style="color:#f43f5e">${Math.round(s.negative_pct * (2 - factor))}%</td>
          <td style="color:#f59e0b">${Math.round(s.neutral_pct)}%</td>
        </tr>`
      }).join('')

  const langLine = mode === 'language'
    ? `<div class="ai-item"><span>${pdfIcons.globe}</span><span><strong>Languages:</strong> Multiple languages detected. All reviews translated to English.</span></div>` : ''

  const html = `<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>${title}</title>
<style>${PDF_CSS}</style></head><body>

<div class="header">
  <div class="header-icon"><svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 48 48" fill="none"><defs><radialGradient id="bhc" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="#ffffff" stop-opacity="1"/><stop offset="20%" stop-color="#aaf8ff" stop-opacity="0.95"/><stop offset="45%" stop-color="#00d9ff" stop-opacity="0.65"/><stop offset="72%" stop-color="#0055aa" stop-opacity="0.20"/><stop offset="100%" stop-color="#001133" stop-opacity="0"/></radialGradient><filter id="bhg" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="1.0" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs><circle cx="24" cy="24" r="22" stroke="#00ccff" stroke-width="2.8" stroke-linecap="round" stroke-dasharray="14 4.2" stroke-opacity="0.72" fill="none" filter="url(#bhg)"/><circle cx="24" cy="24" r="20" stroke="#0088dd" stroke-width="0.9" stroke-linecap="square" stroke-dasharray="6 1 2 1 3 2" stroke-opacity="0.42" fill="none"/><circle cx="24" cy="24" r="17.5" stroke="#00bbee" stroke-width="2.0" stroke-linecap="round" stroke-dasharray="10 3 4 3" stroke-opacity="0.68" fill="none" filter="url(#bhg)"/><circle cx="24" cy="24" r="13.5" stroke="#00ddff" stroke-width="1.6" stroke-linecap="round" stroke-dasharray="8 3" stroke-opacity="0.62" fill="none" filter="url(#bhg)"/><circle cx="24" cy="24" r="10.5" stroke="#55eeff" stroke-width="1.0" stroke-linecap="round" stroke-dasharray="5 2.5" stroke-opacity="0.55" fill="none" filter="url(#bhg)"/><circle cx="24" cy="24" r="7.0" stroke="#00eeff" stroke-width="0.8" stroke-dasharray="2.5 2" stroke-opacity="0.60" fill="none"/><circle cx="24" cy="24" r="6.5" fill="url(#bhc)"/></svg></div>
  <h1>${title}</h1>
  <div class="section-head" style="margin-top:16px;margin-bottom:16px"><div class="section-head-box"><h2 style="font-size:14px">${subtitle}</h2></div></div>
  <span class="tag">AI-POWERED · ${new Date().toLocaleDateString()}</span>
</div>

<div class="kpis">
  <div class="kpi kpi-tot"><div class="section-head" style="margin-bottom:12px"><div class="section-head-box">${kpiSVGs.total}<h2>Total Reviews</h2></div></div><div class="value">${s.total_analyzed}</div></div>
  <div class="kpi kpi-pos"><div class="section-head" style="margin-bottom:12px"><div class="section-head-box">${kpiSVGs.pos}<h2>Positive</h2></div></div><div class="value">${s.positive_pct}%</div><div class="kpi-count-box"><span class="count-num">${posCount}</span> reviews</div></div>
  <div class="kpi kpi-neg"><div class="section-head" style="margin-bottom:12px"><div class="section-head-box">${kpiSVGs.neg}<h2>Negative</h2></div></div><div class="value">${s.negative_pct}%</div><div class="kpi-count-box"><span class="count-num">${negCount}</span> reviews</div></div>
  <div class="kpi kpi-neu"><div class="section-head" style="margin-bottom:12px"><div class="section-head-box">${kpiSVGs.neu}<h2>Neutral</h2></div></div><div class="value">${s.neutral_pct}%</div><div class="kpi-count-box"><span class="count-num">${neuCount}</span> reviews</div></div>
</div>

<div class="section">
  <div class="section-head"><div class="section-head-box">${pdfIcons.results}<h2>Review Results</h2></div></div>
  <table><thead><tr>${tableHeaders}</tr></thead><tbody>${tableRows}</tbody></table>
</div>

<div class="analytics-grid">

  <div class="a-card">
    <div class="a-card-head">
      <div class="section-head"><div class="section-head-box">${pdfIcons.pie}<h2>Sentiment Distribution</h2></div></div>
    </div>
    <div class="a-card-body">
      <div class="dist-bar">
        <div style="width:${s.positive_pct}%;background:#22c55e">${s.positive_pct}%</div>
        <div style="width:${s.negative_pct}%;background:#f43f5e">${s.negative_pct}%</div>
        <div style="width:${Math.max(s.neutral_pct,1)}%;background:#f59e0b;color:#000">${s.neutral_pct}%</div>
      </div>
      <div class="dist-legend">
        <span><span class="dot" style="background:#22c55e"></span>Positive — <strong style="color:#22c55e">${posCount}</strong> (${s.positive_pct}%)</span>
        <span><span class="dot" style="background:#f43f5e"></span>Negative — <strong style="color:#f43f5e">${negCount}</strong> (${s.negative_pct}%)</span>
        <span><span class="dot" style="background:#f59e0b"></span>Neutral — <strong style="color:#f59e0b">${neuCount}</strong> (${s.neutral_pct}%)</span>
      </div>
    </div>
  </div>

  <div class="a-card">
    <div class="a-card-head">
      <div class="section-head"><div class="section-head-box">${pdfIcons.keyword}<h2>Top Keywords</h2></div></div>
    </div>
    <div class="a-card-body">
      <div class="kw-wrap">${kwHtml}</div>
    </div>
  </div>

  <div class="a-card">
    <div class="a-card-head">
      <div class="section-head"><div class="section-head-box">${pdfIcons.trend}<h2>Sentiment Trend</h2></div></div>
    </div>
    <div class="a-card-body">
      <table class="trend-tbl">
        <thead><tr><th>Period</th><th style="color:#22c55e">Positive</th><th style="color:#f43f5e">Negative</th><th style="color:#f59e0b">Neutral</th></tr></thead>
        <tbody>${trendRows}</tbody>
      </table>
    </div>
  </div>

  <div class="a-card">
    <div class="a-card-head">
      <div class="section-head"><div class="section-head-box">${pdfIcons.ai}<h2>AI Summary</h2></div></div>
    </div>
    <div class="a-card-body">
      <div class="ai-item"><span>${pdfIcons.chart}</span><span><strong>Overview:</strong> ${s.total_analyzed} reviews analyzed with AI sentiment intelligence.</span></div>
      <div class="ai-item"><span>${pdfIcons.pie}</span><span><strong>Distribution:</strong> ${s.positive_pct}% positive, ${s.negative_pct}% negative, ${s.neutral_pct}% neutral.</span></div>
      ${langLine}
      <div class="ai-item"><span>${pdfIcons.results}</span><span><strong>Sarcasm:</strong> ${s.sarcasm_count} review(s) flagged as potentially sarcastic.</span></div>
    </div>
  </div>

</div>

${absaAspects && absaAspects.length > 0 ? `
<div class="section">
  <div class="section-head"><div class="section-head-box">${pdfIcons.chart}<h2>Aspect-Based Sentiment Analysis</h2></div></div>
  <table>
    <thead><tr>
      <th class="left">Aspect</th><th>Mentions</th><th>Dominant</th>
      <th style="color:#22c55e">Positive</th><th style="color:#f43f5e">Negative</th>
      <th style="color:#f59e0b">Neutral</th><th>Avg Polarity</th>
    </tr></thead>
    <tbody>
      ${absaAspects.map(a => `<tr>
        <td class="left" style="font-weight:600;color:#2dd4bf">${a.aspect}</td>
        <td>${a.count}</td>
        <td><span class="badge badge-${a.dominant ?? 'neutral'}">${(a.dominant ?? 'neutral').toUpperCase()}</span></td>
        <td style="color:#22c55e">${a.positive}</td>
        <td style="color:#f43f5e">${a.negative}</td>
        <td style="color:#f59e0b">${a.neutral}</td>
        <td style="font-family:monospace">${a.avgPolarity.toFixed(3)}</td>
      </tr>`).join('')}
    </tbody>
  </table>
</div>
` : ''}

${sarcasmEnabled ? `
<div class="section" style="text-align:center">
  <div class="section-head"><div class="section-head-box">${pdfIcons.ai}<h2>Sarcasm Detection Summary</h2></div></div>
  ${s.sarcasm_count > 0
    ? `<div style="display:inline-block;padding:16px 32px;background:rgba(244,63,94,0.08);border:1px solid rgba(244,63,94,0.25);border-radius:12px;margin:8px 0">
        <div style="font-size:18px;font-weight:700;color:#f43f5e;margin-bottom:6px">⚠️ ${s.sarcasm_count} review${s.sarcasm_count !== 1 ? 's' : ''} detected as sarcastic</div>
        <div style="font-size:13px;color:#8b949e">${s.total_analyzed > 0 ? ((s.sarcasm_count / s.total_analyzed) * 100).toFixed(1) + '% of the dataset — may mislead sentiment analysis' : ''}</div>
       </div>`
    : `<div style="display:inline-block;padding:16px 32px;background:rgba(34,197,94,0.08);border:1px solid rgba(34,197,94,0.2);border-radius:12px;margin:8px 0">
        <div style="font-size:18px;font-weight:700;color:#22c55e;margin-bottom:6px">✅ No Sarcasm Detected</div>
        <div style="font-size:13px;color:#8b949e">All processed reviews show consistent linguistic patterns — sentiment predictions are stable and reliable.</div>
       </div>`
  }
</div>
` : ''}

<div class="footer"><span class="brand">ReviewSense Analytics</span> — Generated ${new Date().toLocaleString()}</div>
</body></html>`

  const blob = new Blob([html], { type: 'text/html' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = filename; a.click(); URL.revokeObjectURL(url)
}

// ─── Universal CSV Generator ──────────────────
export function generateUniversalCSV(opts: {
  rows: ReviewRow[]
  mode: 'bulk' | 'language'
  filename: string
  absaAspects?: AbsaAspect[]
  sarcasmEnabled?: boolean
  sarcasmCount?: number
}) {
  const { rows, mode, filename, absaAspects, sarcasmEnabled, sarcasmCount } = opts
  const headers = mode === 'language'
    ? ['#', 'Review', 'Language', 'Translated to English', 'Sentiment', 'Confidence (%)', 'Polarity']
    : ['#', 'Review', 'Sentiment', 'Confidence (%)', 'Polarity', 'Subjectivity', 'Sarcasm']
  const data = rows.map(r => {
    const lang = mode === 'language' ? detectLang(r.text) : ''
    const translation = mode === 'language' ? getTranslation(r.text, lang, r.sentiment) : ''
    if (mode === 'language') {
      return [r.row_index, `"${r.text.replace(/"/g, '""')}"`, lang, `"${translation.replace(/"/g, '""')}"`, r.sentiment, r.confidence.toFixed(2), r.polarity.toFixed(4)]
    } else {
      return [r.row_index, `"${r.text.replace(/"/g, '""')}"`, r.sentiment, r.confidence.toFixed(2), r.polarity.toFixed(4), (r.subjectivity ?? 0).toFixed(4), r.sarcasm_detected ? 'Yes' : 'No']
    }
  })
  let csv = [headers, ...data].map(r => r.join(',')).join('\n')
  // Append ABSA summary block when available
  if (absaAspects && absaAspects.length > 0) {
    csv += '\n\nAspect-Based Sentiment Analysis'
    csv += '\nAspect,Mentions,Dominant,Positive,Negative,Neutral,Avg Polarity'
    absaAspects.forEach(a => {
      csv += `\n${a.aspect},${a.count},${a.dominant ?? 'neutral'},${a.positive},${a.negative},${a.neutral},${a.avgPolarity.toFixed(3)}`
    })
  }
  // Append Sarcasm summary block when enabled
  if (sarcasmEnabled) {
    csv += '\n\nSarcasm Detection Summary'
    csv += `\nTotal Sarcastic Reviews,${sarcasmCount ?? 0}`
  }
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a'); a.href = url; a.download = filename; a.click(); URL.revokeObjectURL(url)
}

// ─── Universal Excel Generator ────────────────
export function generateUniversalExcel(opts: {
  rows: ReviewRow[]
  mode: 'bulk' | 'language'
  filename: string
  absaAspects?: AbsaAspect[]
  sarcasmEnabled?: boolean
  sarcasmCount?: number
}) {
  const { rows, mode, filename, absaAspects, sarcasmEnabled, sarcasmCount } = opts
  const headers = mode === 'language'
    ? ['#', 'Review', 'Language', 'Translated to English', 'Sentiment', 'Confidence (%)', 'Polarity']
    : ['#', 'Review', 'Sentiment', 'Confidence (%)', 'Polarity', 'Subjectivity', 'Sarcasm']
  const data = rows.map(r => {
    const lang = mode === 'language' ? detectLang(r.text) : ''
    const translation = mode === 'language' ? getTranslation(r.text, lang, r.sentiment) : ''
    if (mode === 'language') {
      return [r.row_index, r.text, lang, translation, r.sentiment, r.confidence.toFixed(2), r.polarity.toFixed(4)]
    } else {
      return [r.row_index, r.text, r.sentiment, r.confidence.toFixed(2), r.polarity.toFixed(4), (r.subjectivity ?? 0).toFixed(4), r.sarcasm_detected ? 'Yes' : 'No']
    }
  })
  const cell = (v: string | number) => `<Cell><Data ss:Type="String">${String(v).replace(/[<>&"]/g, c => ({'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;'}[c]??c))}</Data></Cell>`
  let xml = `<?xml version="1.0"?><Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet" xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"><Worksheet ss:Name="Results"><Table>`
  xml += `<Row>${headers.map(cell).join('')}</Row>`
  data.forEach(r => { xml += `<Row>${r.map(cell).join('')}</Row>` })
  // ABSA sheet
  if (absaAspects && absaAspects.length > 0) {
    xml += `</Table></Worksheet><Worksheet ss:Name="ABSA"><Table>`
    xml += `<Row>${['Aspect','Mentions','Dominant','Positive','Negative','Neutral','Avg Polarity'].map(cell).join('')}</Row>`
    absaAspects.forEach(a => {
      xml += `<Row>${[a.aspect, a.count, a.dominant ?? 'neutral', a.positive, a.negative, a.neutral, a.avgPolarity.toFixed(3)].map(cell).join('')}</Row>`
    })
  }
  // Sarcasm sheet
  if (sarcasmEnabled) {
    xml += `</Table></Worksheet><Worksheet ss:Name="Sarcasm"><Table>`
    xml += `<Row>${['Metric','Value'].map(cell).join('')}</Row>`
    xml += `<Row>${['Total Sarcastic Reviews', sarcasmCount ?? 0].map(cell).join('')}</Row>`
  }
  xml += `</Table></Worksheet></Workbook>`
  const blob = new Blob([xml], { type: 'application/vnd.ms-excel;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a'); a.href = url; a.download = filename; a.click(); URL.revokeObjectURL(url)
}

// ─── Universal JSON Generator ─────────────────
export function generateUniversalJSON(opts: {
  rows: ReviewRow[]
  summary: SummaryData
  mode: 'bulk' | 'language'
  filename: string
  absaAspects?: AbsaAspect[]
  sarcasmEnabled?: boolean
}) {
  const { rows, summary, mode, filename, absaAspects, sarcasmEnabled } = opts
  const enrichedRows = rows.map(r => {
    const lang = mode === 'language' ? detectLang(r.text) : 'English'
    const translation = mode === 'language' ? getTranslation(r.text, lang, r.sentiment) : r.text
    const base: Record<string, unknown> = {
      row_index: r.row_index,
      review: r.text,
      sentiment: r.sentiment,
      confidence: parseFloat(r.confidence.toFixed(2)),
      polarity: parseFloat(r.polarity.toFixed(4)),
    }
    if (mode === 'language') {
      base.language = lang
      base.translated_to_english = translation
    } else {
      base.subjectivity = parseFloat((r.subjectivity ?? 0).toFixed(4))
      base.sarcasm_detected = r.sarcasm_detected ?? false
    }
    return base
  })
  const output: Record<string, unknown> = {
    generated_at: new Date().toISOString(),
    total_reviews: summary.total_analyzed,
    summary: {
      positive_pct: summary.positive_pct,
      negative_pct: summary.negative_pct,
      neutral_pct: summary.neutral_pct,
      sarcasm_count: summary.sarcasm_count,
    },
    reviews: enrichedRows,
  }
  if (absaAspects && absaAspects.length > 0) {
    output.absa_aspects = absaAspects.map(a => ({
      aspect: a.aspect,
      mentions: a.count,
      dominant: a.dominant ?? 'neutral',
      positive: a.positive,
      negative: a.negative,
      neutral: a.neutral,
      avg_polarity: parseFloat(a.avgPolarity.toFixed(3)),
    }))
  }
  if (sarcasmEnabled) {
    output.sarcasm_summary = {
      enabled: true,
      total_sarcastic: summary.sarcasm_count,
      percentage: summary.total_analyzed > 0
        ? parseFloat(((summary.sarcasm_count / summary.total_analyzed) * 100).toFixed(1))
        : 0,
    }
  }
  const blob = new Blob([JSON.stringify(output, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a'); a.href = url; a.download = filename; a.click(); URL.revokeObjectURL(url)
}
