"""
backend/services/llm_service.py
===============================
LLM Advisory Report generation service for Module 14.
Powered by Groq API (openai/gpt-oss-120b) with strict JSON output.

Key Principles:
  1. Downstream from MobileNetV2: Accepts ML diagnosis as immutable truth.
  2. Context-Aware: Connects farm location & Open-Meteo weather to disease advice.
  3. Safe Agronomic Guidance: Forbids fabricated chemical brand names and dosages;
     focuses on cultural, mechanical, and bio-friendly management while delegating
     regulated chemical interventions to local Krishi Vigyan Kendra (KVK) specialists.
  4. Resilient: Validates schema via Pydantic; provides safe graceful fallback if API is unreachable.
"""

import asyncio
from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, Optional

import httpx

import config
from schemas import ReportStructuredResponse

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self._override_keys = None
        self.model = getattr(config, "GROQ_MODEL", "openai/gpt-oss-120b")
        self.api_url = getattr(
            config, "GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions"
        )
        self.timeout = getattr(config, "GROQ_TIMEOUT_SECONDS", 45.0)

    def set_keys_for_testing(self, key_list: list):
        """Allows test suites to inject keys with aliases without touching config."""
        self._override_keys = [
            {"alias": f"key_{i+1}", "key": k} for i, k in enumerate(key_list)
        ]

    def get_configured_keys(self) -> list:
        """Returns list of configured Groq keys with safe aliases (key_1, key_2, key_3)."""
        if self._override_keys is not None:
            return self._override_keys

        keys = []
        k1 = getattr(config, "GROQ_API_KEY_1", "") or getattr(config, "GROQ_API_KEY", "")
        if k1 and k1.strip():
            keys.append({"alias": "key_1", "key": k1.strip()})

        k2 = getattr(config, "GROQ_API_KEY_2", "")
        if k2 and k2.strip():
            keys.append({"alias": "key_2", "key": k2.strip()})

        k3 = getattr(config, "GROQ_API_KEY_3", "")
        if k3 and k3.strip():
            keys.append({"alias": "key_3", "key": k3.strip()})

        return keys

    def _build_system_prompt(self, target_lang: str) -> str:
        lang_note = {
            "hi": (
                "Translate and output all content strictly in standard Hindi (हिन्दी script). "
                "Provide accurate, natural agricultural terms (e.g. सफेद धब्बा रोग, पत्ती, तना, जैविक नियंत्रण, "
                "नीम का अर्क/तेल, पीले चिपचिपे कार्ड/ट्रैप). Never output transliterated Latin characters."
            ),
            "gu": (
                "Translate and output all content strictly in standard Gujarati (ગુજરાતી script). "
                "Provide authentic Gujarati agricultural terms (e.g. સફેદ દાગ, પાંદડાં, જીવાત, જૈવિક નિયંત્રણ, "
                "લીંબોળીનું અર્ક/તેલ, પીળા ચીકણા ટ્રેપ). Never output transliterated Latin characters."
            ),
            "en": "Output all content in clear, accessible English.",
        }.get(target_lang, "Output in English.")

        return f"""You are an authoritative agricultural extension agronomist and plant pathologist assisting farmers.
Language instruction: {lang_note}

MANDATORY DIRECTIVES:
1. THE ML DIAGNOSIS IS THE SOURCE OF TRUTH. MobileNetV2 has already diagnosed the disease from leaf imagery. Do NOT second-guess, replace, or alter the identified disease name. Focus entirely on explaining symptoms and actionable advisory.
2. INTEGRATE WEATHER & LOCATION: Directly link the farm's location (State, District, Village) and current weather (temperature, humidity, rainfall, wind) to explain disease development, spore germination, vector spread, or crop stress.
3. CHEMICAL REGULATION & SAFETY RULE:
   - Do NOT invent, fabricate, or recommend proprietary chemical pesticide/fungicide brand names, commercial formulations, or specific dosage rates.
   - Emphasize cultural management, pruning, field sanitation, airflow, drainage, and gentle organic/biological methods (e.g. neem cake/oil, yellow sticky traps).
   - Advise consulting the nearest Krishi Vigyan Kendra (KVK) or district agricultural extension officer before applying scheduled chemical treatments.
4. STRICT JSON FORMAT: Output ONLY a valid JSON object matching this exact schema:
{{
  "disease_name": "string (localized disease name)",
  "confidence_interpretation": "string (clear interpretation of the confidence percentage for a farmer)",
  "summary": "string (2-3 concise actionable sentences summarizing diagnosis & environmental risk)",
  "symptoms": ["string", "string", ...],
  "possible_causes": ["string (link to weather/environmental causes)", ...],
  "local_context": "string (regional & micro-climate context for the farm)",
  "management_steps": ["string (cultural/mechanical/sanitation actions)", ...],
  "prevention_steps": ["string (field hygiene, crop rotation, soil care)", ...],
  "warning_signs": ["string (escalation triggers requiring expert inspection)", ...],
  "expert_verification_recommended": boolean,
  "disclaimer": "string (formal advisory disclaimer referencing local agricultural university/KVK guidance)"
}}
"""

    def _build_user_prompt(
        self,
        crop: str,
        disease_name: str,
        confidence: float,
        farm_info: Optional[Dict[str, Any]],
        weather_info: Optional[Dict[str, Any]],
    ) -> str:
        loc_str = "Location not specified"
        if farm_info:
            parts = [
                farm_info.get("village"),
                farm_info.get("district"),
                farm_info.get("state"),
            ]
            valid_parts = [p for p in parts if p]
            if valid_parts:
                loc_str = ", ".join(valid_parts)
            if farm_info.get("latitude") and farm_info.get("longitude"):
                loc_str += f" (GPS: {farm_info['latitude']:.4f}, {farm_info['longitude']:.4f})"

        wx_str = "No meteorological station linked"
        if weather_info and weather_info.get("temperature_c") is not None:
            wx_str = (
                f"Temp: {weather_info.get('temperature_c')}°C | "
                f"Humidity: {weather_info.get('humidity_pct')}% | "
                f"Precipitation: {weather_info.get('rainfall_mm', 0.0)} mm | "
                f"Wind: {weather_info.get('wind_speed_kmh')} km/h | "
                f"Condition: '{weather_info.get('weather_condition', 'Normal')}'"
            )

        return f"""Generate a localized agricultural advisory report for the following diagnostic event:

DIAGNOSTIC EVENT:
- Crop: {crop.capitalize()}
- Authoritative ML Diagnosis: {disease_name}
- Softmax Confidence: {confidence * 100:.1f}% ({confidence:.4f})

FARM & ENVIRONMENTAL CONTEXT:
- Farm Region: {loc_str}
- Current Weather Snapshot: {wx_str}

Please generate the complete, structured, JSON-only advisory report."""

    def _generate_fallback_report(
        self,
        crop: str,
        disease_name: str,
        confidence: float,
        farm_info: Optional[Dict[str, Any]],
        weather_info: Optional[Dict[str, Any]],
        target_lang: str = "en",
    ) -> ReportStructuredResponse:
        """Safe agronomic fallback report if the LLM provider times out or fails."""
        is_healthy = "healthy" in disease_name.lower()
        district = (
            farm_info.get("district")
            if farm_info and farm_info.get("district")
            else "your local district"
        )
        temp_c = weather_info.get("temperature_c") if weather_info else None
        norm_crop = crop.capitalize()

        # Hindi (hi) fallback template
        if target_lang == "hi":
            temp_text_hi = (
                f"वर्तमान तापमान {temp_c}°C है"
                if temp_c is not None
                else "सामान्य मौसमी तापमान"
            )
            dist_hi = district if district != "your local district" else "आपके स्थानीय क्षेत्र"
            if is_healthy:
                return ReportStructuredResponse(
                    disease_name=f"स्वस्थ {norm_crop} की पत्ती (Healthy)",
                    confidence_interpretation=(
                        f"न्यूरल मॉडल ने {confidence * 100:.1f}% विश्वास के साथ स्वस्थ पत्ती की पुष्टि की है।"
                    ),
                    summary=(
                        f"आपकी {norm_crop} फसल की पत्तियां सामान्य और स्वस्थ दिख रही हैं। {temp_text_hi}। नियमित सिंचाई और पोषण प्रबंधन जारी रखें।"
                    ),
                    symptoms=[
                        "समान बनावट वाली हरी पत्तियां",
                        "कोई धब्बा, सड़न या कीट क्षति नहीं देखी गई",
                    ],
                    possible_causes=[
                        "संतुलित पोषण और उचित मृदा नमी प्रबंधन"
                    ],
                    local_context=f"{dist_hi} में {norm_crop} की खेती के लिए अनुकूल मौसम।",
                    management_steps=[
                        "फसल की वृद्धि के अनुसार संतुलित एन-पी-के उर्वरक जारी रखें",
                        "जलभराव से बचते हुए नियमित सिंचाई बनाए रखें",
                        "कीटों या कवक के शुरुआती लक्षणों के लिए साप्ताहिक पत्ती निरीक्षण करें",
                    ],
                    prevention_steps=[
                        "नियमित रूप से खेत की निगरानी बनाए रखें",
                        "खेत की मेड़ों को खरपतवार मुक्त रखें ताकि कीट न पनपें",
                    ],
                    warning_signs=[
                        "तेज धूप में पत्तियों का अचानक पीला पड़ना या मुरझाना",
                        "नई पत्तियों पर चित्तीदार निशान या मुड़न दिखना",
                    ],
                    expert_verification_recommended=False,
                    disclaimer=(
                        "यह स्वचालित सलाह केवल संदर्भ के लिए है। प्रमाणित कृषि सलाह के लिए अपने नजदीकी कृषि विज्ञान केंद्र (KVK) से संपर्क करें।"
                    ),
                )
            else:
                return ReportStructuredResponse(
                    disease_name=f"{disease_name} (पहचाना गया रोग)",
                    confidence_interpretation=(
                        f"मॉडल ने {confidence * 100:.1f}% सटीकता के साथ {disease_name} के लक्षण पहचाने हैं।"
                    ),
                    summary=(
                        f"आपकी {norm_crop} फसल पर {disease_name} के लक्षण पहचाने गए हैं। {dist_hi} में संक्रमण रोकने के लिए तुरंत स्वच्छता उपाय अपनाएं।"
                    ),
                    symptoms=[
                        f"{disease_name} के कारण पत्तियों पर धब्बे, विकृति या रंग परिवर्तन",
                        "प्रभावित पत्तियों पर जैविक तनाव के संकेत",
                    ],
                    possible_causes=[
                        f"रोग के अनुकूल मौसमी परिस्थितियां ({temp_text_hi})",
                        "फसल छत्रक में अधिक नमी या कीट वाहक गतिविधि",
                    ],
                    local_context=f"वर्तमान मौसम में {dist_hi} के {norm_crop} खेतों में देखा जाने वाला सामान्य संक्रमण।",
                    management_steps=[
                        "गंभीर रूप से प्रभावित पत्तियों को तोड़कर खेत से दूर सुरक्षित नष्ट करें",
                        "संक्रमण फैलने से रोकने के लिए औजारों को साफ रखें",
                        "पत्तियों को रात भर गीला रखने वाली अतिरिक्त सिंचाई से बचें",
                        "जैविक रोकथाम हेतु 5% नीम अर्क या नीम तेल का छिड़काव करें",
                    ],
                    prevention_steps=[
                        "हवा के बेहतर संचार के लिए पौधों के बीच उचित दूरी रखें",
                        "अगले मौसम में गैर-पोषक फसलों के साथ फसल चक्र अपनाएं",
                        "प्रमाणित रोग-प्रतिरोधी बीजों का उपयोग करें",
                    ],
                    warning_signs=[
                        "20% से अधिक पौधों पर तेजी से धब्बों या सिकुड़न का प्रसार",
                        "तनों, फूलों या फलों पर घाव या सड़न दिखना",
                    ],
                    expert_verification_recommended=True,
                    disclaimer=(
                        "यह स्वचालित रिपोर्ट केवल सांस्कृतिक और निवारक मार्गदर्शन प्रदान करती है। अधिकृत कृषि विस्तार अधिकारी या KVK की सलाह के बिना रासायनिक कीटनाशकों का प्रयोग न करें।"
                    ),
                )

        # Gujarati (gu) fallback template
        elif target_lang == "gu":
            temp_text_gu = (
                f"હાલનું તાપમાન {temp_c}°C છે"
                if temp_c is not None
                else "સામાન્ય મોસમી તાપમાન"
            )
            dist_gu = district if district != "your local district" else "તમારા વિસ્તાર"
            if is_healthy:
                return ReportStructuredResponse(
                    disease_name=f"તંદુરસ્ત {norm_crop} પર્ણ (Healthy)",
                    confidence_interpretation=(
                        f"ન્યુરલ મોડેલે {confidence * 100:.1f}% વિશ્વસનીયતા સાથે તંદુરસ્ત પાંદડાની પુષ્ટિ કરી છે."
                    ),
                    summary=(
                        f"તમારા {norm_crop} પાક પર પાંદડા સ્વસ્થ અને સામાન્ય જણાય છે. {temp_text_gu}. નિયમિત પિયત અને પોષણ જાળવી રાખો."
                    ),
                    symptoms=[
                        "એકસરખા રંગ અને બનાવટવાળા લીલા પાંદડા",
                        "કોઈ ડાઘ, સડો કે જીવાતના નુકસાનના લક્ષણો નથી",
                    ],
                    possible_causes=[
                        "જમીનમાં યોગ્ય પોષક તત્વો અને ભેજનું સંતુલન"
                    ],
                    local_context=f"{dist_gu} વિસ્તારમાં {norm_crop} પાક માટે અનુકૂળ હવામાન.",
                    management_steps=[
                        "પાકના વિકાસના તબક્કા મુજબ સંતુલિત ખાતર આપવાનું ચાલુ રાખો",
                        "પાણી ભરાઈ ન રહે તે રીતે નિયમિત પિયત આપો",
                        "દર અઠવાડિયે પાંદડાની નીચે જીવાત કે ફૂગના ચિહ્નો તપાસો",
                    ],
                    prevention_steps=[
                        "નિયમિતપણે ખેતરનું નિરીક્ષણ કરો",
                        "શેઢા-પાળા પરથી નીંદણ દૂર રાખો જેથી ચૂસિયા જીવાતો ન ફેલાય",
                    ],
                    warning_signs=[
                        "વધુ ગરમી દરમિયાન પાંદડા અચાનક પીળા પડવા કે કરમાઈ જવા",
                        "નવી ફૂટ પર છાંટવાળા ડાઘ કે પાન કોકડાવું",
                    ],
                    expert_verification_recommended=False,
                    disclaimer=(
                        "આ સ્વચાલિત સલાહ ખેડૂત સંદર્ભ માટે છે. પ્રમાણિત કૃષિ માર્ગદર્શન માટે નજીકના કૃષિ વિજ્ઞાન કેન્દ્ર (KVK) નો સંપર્ક કરો."
                    ),
                )
            else:
                return ReportStructuredResponse(
                    disease_name=f"{disease_name} (ઓળખાયેલ રોગ)",
                    confidence_interpretation=(
                        f"મોડેલે {confidence * 100:.1f}% ચોકસાઈ સાથે {disease_name} ના લક્ષણો ઓળખ્યા છે."
                    ),
                    summary=(
                        f"તમારા {norm_crop} પાક પર {disease_name} ના લક્ષણો જણાયા છે. {dist_gu} વિસ્તારમાં રોગ વધુ ન ફેલાય તે માટે ખેતરમાં યોગ્ય સ્વચ્છતા રાખો."
                    ),
                    symptoms=[
                        f"{disease_name} ના કારણે પાંદડા પર ડાઘ, રંગ પરિવર્તન અથવા વિકૃતિ",
                        "અસરગ્રસ્ત પર્ણો પર નબળાઈના સંકેતો",
                    ],
                    possible_causes=[
                        f"રોગના ફેલાવા માટે અનુકૂળ હવામાન ({temp_text_gu})",
                        "છોડ વચ્ચે વધુ પડતો ભેજ અથવા ચૂસિયા જીવાતોની હાજરી",
                    ],
                    local_context=f"ચાલુ ઋતુમાં {dist_gu} ના {norm_crop} ખેતરોમાં જોવા મળતો ચેપ.",
                    management_steps=[
                        "વધુ બગડેલા પાંદડા તોડીને ખેતરથી દૂર સુરક્ષિત રીતે નષ્ટ કરો",
                        "રોગ ફેલાતો અટકાવવા કાપણીના સાધનો સાફ રાખો",
                        "સાંજના સમયે પાંદડા ભીના રહે તેવું વધુ પિયત ટાળો",
                        "જૈવિક નિયંત્રણ માટે 5% લીંબોળીના અર્ક અથવા લીમડાના તેલનો છંટકાવ કરો",
                    ],
                    prevention_steps=[
                        "હવાની અવરજવર માટે છોડ વચ્ચે યોગ્ય અંતર રાખો",
                        "આગામી સિઝનમાં પાકની ફેરબદલી કરો",
                        "પ્રમાણિત અને રોગપ્રતિકારક બિયારણ વાપરો",
                    ],
                    warning_signs=[
                        "20% થી વધુ છોડ પર રોગનો ઝડપી ફેલાવો",
                        "ડાળીઓ, ફૂલો કે મરચાં પર ડાઘ કે સડો દેખાવો",
                    ],
                    expert_verification_recommended=True,
                    disclaimer=(
                        "આ સ્વચાલિત સલાહ પદ્ધતિસરના માર્ગદર્શન માટે છે. કૃષિ અધિકારી અથવા KVK ની મંજૂરી વિના કૃત્રિમ રાસાયણિક જંતુનાશકોનો ઉપયોગ કરશો નહીં."
                    ),
                )

        # Default: English (en) fallback template
        temp_text = (
            f"Current temperature is {temp_c}°C"
            if temp_c is not None
            else "Normal seasonal temperatures"
        )

        if is_healthy:
            return ReportStructuredResponse(
                disease_name=f"Healthy {norm_crop} Foliage",
                confidence_interpretation=(
                    f"The neural model confirmed healthy leaf characteristics with {confidence * 100:.1f}% confidence."
                ),
                summary=(
                    f"Your {crop} plants show normal leaf coloration and vigor without evident symptoms. "
                    f"{temp_text}. Maintain routine irrigation and nutrient schedules."
                ),
                symptoms=[
                    "Vibrant green leaf blade with uniform texture",
                    "No spots, necrotic margins, or insect curling detected",
                ],
                possible_causes=[
                    "Adequate plant nutrition and appropriate soil moisture balance"
                ],
                local_context=f"Favorable conditions observed for {crop} cultivation in {district}.",
                management_steps=[
                    "Continue balanced N-P-K fertilization according to crop growth stage",
                    "Maintain regular drip or furrow irrigation without waterlogging",
                    "Inspect under leaves weekly for early signs of pests or fungal spots",
                ],
                prevention_steps=[
                    "Practice regular field scouting",
                    "Keep plot edges free of weeds that harbor sucking pests",
                ],
                warning_signs=[
                    "Sudden yellowing or wilting during hot dry spells",
                    "Appearance of mottled patterns or curling on new flushes",
                ],
                expert_verification_recommended=False,
                disclaimer=(
                    "This advisory report is generated as an automated agricultural reference tool. "
                    "For certified agronomy assistance, consult your local Krishi Vigyan Kendra (KVK)."
                ),
            )
        else:
            return ReportStructuredResponse(
                disease_name=disease_name,
                confidence_interpretation=(
                    f"The model identified symptom markers characteristic of {disease_name} "
                    f"with {confidence * 100:.1f}% confidence."
                ),
                summary=(
                    f"Visible leaf lesions consistent with {disease_name} were identified on your {crop} crop. "
                    f"Under local conditions in {district}, prompt field sanitation is recommended to protect surrounding foliage."
                ),
                symptoms=[
                    f"Lesions, discoloration, or leaf distortion indicative of {disease_name}",
                    "Signs of foliar stress on affected leaves",
                ],
                possible_causes=[
                    f"Favorable weather conditions facilitating disease manifestation ({temp_text})",
                    "Microclimatic humidity or vector activity within the crop canopy",
                ],
                local_context=f"Commonly observed in {crop} plots across {district} during this season.",
                management_steps=[
                    "Isolate and carefully remove heavily damaged leaves from the field",
                    "Sanitize pruning knives and shears between rows to avoid cross-contamination",
                    "Adjust irrigation timing to avoid keeping leaf surfaces wet overnight",
                    "Consult your local agricultural extension officer for approved regional interventions",
                ],
                prevention_steps=[
                    "Ensure adequate row spacing to improve air circulation through the canopy",
                    "Rotate crops with non-host species in subsequent planting seasons",
                    "Use certified disease-tolerant seed varieties",
                ],
                warning_signs=[
                    "Rapid spread of spots or curling across more than 20% of plants",
                    "Lesions appearing on stems, flowers, or fruit pods",
                ],
                expert_verification_recommended=True,
                disclaimer=(
                    "This automated advisory provides cultural and preventative guidance. "
                    "Do not apply synthetic chemicals without confirmation from a licensed agricultural officer or KVK extension."
                ),
            )

    @property
    def api_key(self) -> str:
        """Backward compatible accessor returning active primary key or empty string."""
        keys = self.get_configured_keys()
        return keys[0]["key"] if keys else ""

    async def generate_advisory_report(
        self,
        crop: str,
        disease_name: str,
        confidence: float,
        farm_info: Optional[Dict[str, Any]] = None,
        weather_info: Optional[Dict[str, Any]] = None,
        target_lang: str = "en",
    ) -> ReportStructuredResponse:
        """
        Query Groq LLM (openai/gpt-oss-120b) for structured agricultural advisory report.
        Supports multi-key rotation across up to 3 accounts with safe fallback.
        """
        keys = self.get_configured_keys()
        if not keys:
            logger.warning("[GroqKeyManager] No Groq API keys configured; serving localized agronomic fallback report")
            return self._generate_fallback_report(
                crop, disease_name, confidence, farm_info, weather_info, target_lang
            )

        system_prompt = self._build_system_prompt(target_lang)
        user_prompt = self._build_user_prompt(
            crop, disease_name, confidence, farm_info, weather_info
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }

        last_error = None
        for key_entry in keys:
            alias = key_entry["alias"]
            secret_key = key_entry["key"]
            headers = {
                "Authorization": f"Bearer {secret_key}",
                "Content-Type": "application/json",
            }

            max_key_attempts = 2
            for attempt in range(max_key_attempts):
                try:
                    logger.info(
                        f"Calling Groq LLM ({self.model}) with key '{alias}' for {crop} - {disease_name} advisory..."
                    )
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        resp = await client.post(self.api_url, headers=headers, json=payload)

                    if resp.status_code == 429:
                        error_detail = ""
                        try:
                            err_json = resp.json().get("error", {})
                            error_detail = err_json.get("message") or err_json.get("code") or "rate_limit_exceeded"
                        except Exception:
                            pass
                        logger.warning(
                            f"[GroqKeyManager] Key '{alias}' hit rate limit / quota exhaustion (HTTP 429: {error_detail}). Rotating to next key if available."
                        )
                        last_error = RuntimeError(f"Key {alias} exhausted (429)")
                        break

                    if resp.status_code in (500, 502, 503, 504):
                        if attempt < max_key_attempts - 1:
                            logger.warning(
                                f"[GroqKeyManager] Transient server error on '{alias}' (HTTP {resp.status_code}). Retrying attempt {attempt + 2}..."
                            )
                            await asyncio.sleep(1.0)
                            continue
                        else:
                            logger.warning(
                                f"[GroqKeyManager] Persistent server error on '{alias}' (HTTP {resp.status_code}). Attempting next key."
                            )
                            last_error = RuntimeError(f"Server error on {alias}")
                            break

                    if resp.status_code >= 400:
                        logger.error(
                            f"[GroqKeyManager] Non-recoverable request error with key '{alias}' (HTTP {resp.status_code}): {resp.text}"
                        )
                        resp.raise_for_status()

                    data = resp.json()
                    choice = data["choices"][0]
                    raw_content = choice["message"]["content"]
                    parsed_json = json.loads(raw_content)

                    validated_report = ReportStructuredResponse.model_validate(parsed_json)
                    logger.info(
                        f"[GroqKeyManager] Successfully generated and validated LLM advisory report using key '{alias}'."
                    )
                    return validated_report

                except httpx.TimeoutException as te:
                    logger.warning(
                        f"[GroqKeyManager] Request timeout with key '{alias}' (attempt {attempt + 1})."
                    )
                    if attempt < max_key_attempts - 1:
                        await asyncio.sleep(1.0)
                        continue
                    last_error = te
                    break
                except httpx.HTTPStatusError as hse:
                    logger.warning(f"[GroqKeyManager] Groq client error: {hse}")
                    return self._generate_fallback_report(
                        crop, disease_name, confidence, farm_info, weather_info, target_lang
                    )
                except Exception as exc:
                    logger.warning(f"[GroqKeyManager] Error with key '{alias}': {exc}")
                    last_error = exc
                    break

        logger.warning(
            f"[GroqKeyManager] All configured Groq keys failed or exhausted ({last_error}); serving localized agronomic fallback report"
        )
        return self._generate_fallback_report(
            crop, disease_name, confidence, farm_info, weather_info, target_lang
        )
