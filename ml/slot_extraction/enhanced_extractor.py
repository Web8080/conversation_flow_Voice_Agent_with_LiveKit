import re
from typing import Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class ExtractedSlot:
    value: Any
    confidence: float
    source: str
    normalized_value: Optional[Any] = None
    needs_confirmation: bool = False


class EnhancedSlotExtractor:
    def __init__(self):
        self.date_patterns = [
            (r"\btomorrow\b", self._parse_tomorrow),
            (r"\btoday\b", self._parse_today),
            (r"\bnext week\b", self._parse_next_week),
            (r"\bnext (\w+day)\b", self._parse_next_weekday),
            (r"\b(\w+day)\b", self._parse_weekday),
            (r"\b(\d{1,2})[/-](\d{1,2})[/-]?(\d{2,4})?\b", self._parse_date_format),
            (r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})(?:st|nd|rd|th)?(?:,?\s+(\d{4}))?\b", self._parse_month_date),
        ]
        
        self.time_patterns = [
            (r"\b(\d{1,2}):(\d{2})\s*(am|pm)\b", self._parse_12hour),
            (r"\b(\d{1,2}):(\d{2})\b", self._parse_24hour),
            (r"\b(\d{1,2})\s*(am|pm)\b", self._parse_hour_only),
            (r"\b(morning|afternoon|evening|noon|midnight)\b", self._parse_time_of_day),
        ]
        
        self.name_patterns = [
            (r"\bmy name is (\w+(?:\s+\w+)?)\b", 0.9),
            (r"\bI'm (\w+(?:\s+\w+)?)\b", 0.85),
            (r"\bit's (\w+(?:\s+\w+)?)\b", 0.75),
            (r"\bthis is (\w+(?:\s+\w+)?)\b", 0.70),
        ]
    
    def extract_date(self, text: str) -> Optional[ExtractedSlot]:
        text_lower = text.lower()
        
        for pattern, parser in self.date_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                try:
                    date_value, confidence = parser(match)
                    if date_value:
                        normalized = date_value.strftime("%Y-%m-%d")
                        return ExtractedSlot(
                            value=normalized,
                            confidence=confidence,
                            source="rules",
                            normalized_value=normalized,
                            needs_confirmation=confidence < 0.8
                        )
                except Exception:
                    continue
        
        return None
    
    def extract_time(self, text: str) -> Optional[ExtractedSlot]:
        text_lower = text.lower()
        
        for pattern, parser in self.time_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                try:
                    time_value, confidence = parser(match)
                    if time_value:
                        normalized = time_value.strftime("%H:%M")
                        return ExtractedSlot(
                            value=normalized,
                            confidence=confidence,
                            source="rules",
                            normalized_value=normalized,
                            needs_confirmation=confidence < 0.8
                        )
                except Exception:
                    continue
        
        return None
    
    def extract_name(self, text: str) -> Optional[ExtractedSlot]:
        text_lower = text.lower()
        
        for pattern, confidence in self.name_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                name = match.group(1).strip().title()
                if self._is_valid_name(name):
                    return ExtractedSlot(
                        value=name,
                        confidence=confidence,
                        source="rules",
                        normalized_value=name,
                        needs_confirmation=confidence < 0.85
                    )
        
        return None
    
    def _parse_tomorrow(self, match) -> Tuple[datetime, float]:
        tomorrow = datetime.now() + timedelta(days=1)
        return tomorrow, 0.95
    
    def _parse_today(self, match) -> Tuple[datetime, float]:
        today = datetime.now()
        return today, 0.95
    
    def _parse_next_week(self, match) -> Tuple[datetime, float]:
        next_week = datetime.now() + timedelta(weeks=1)
        return next_week, 0.85
    
    def _parse_next_weekday(self, match) -> Tuple[datetime, float]:
        weekday_name = match.group(1).lower()
        weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        target_weekday = weekdays.index(weekday_name)
        today = datetime.now()
        days_ahead = (target_weekday - today.weekday() + 7) % 7
        if days_ahead == 0:
            days_ahead = 7
        next_date = today + timedelta(days=days_ahead)
        return next_date, 0.90
    
    def _parse_weekday(self, match) -> Tuple[datetime, float]:
        weekday_name = match.group(1).lower()
        weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        target_weekday = weekdays.index(weekday_name)
        today = datetime.now()
        days_ahead = (target_weekday - today.weekday()) % 7
        if days_ahead == 0:
            return today, 0.85
        next_date = today + timedelta(days=days_ahead)
        return next_date, 0.80
    
    def _parse_date_format(self, match) -> Tuple[datetime, float]:
        parts = match.groups()
        month = int(parts[0])
        day = int(parts[1])
        year = int(parts[2]) if parts[2] else datetime.now().year
        
        if year < 100:
            year += 2000
        
        try:
            date = datetime(year, month, day)
            if date < datetime.now():
                date = date.replace(year=date.year + 1)
            return date, 0.90
        except ValueError:
            return None, 0.0
    
    def _parse_month_date(self, match) -> Tuple[datetime, float]:
        months = {
            "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
            "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12
        }
        
        month_name = match.group(1).lower()
        day = int(match.group(2))
        year = int(match.group(3)) if match.group(3) else datetime.now().year
        
        try:
            date = datetime(year, months[month_name], day)
            if date < datetime.now():
                date = date.replace(year=date.year + 1)
            return date, 0.92
        except ValueError:
            return None, 0.0
    
    def _parse_12hour(self, match) -> Tuple[datetime, float]:
        hour = int(match.group(1))
        minute = int(match.group(2))
        am_pm = match.group(3).lower()
        
        if am_pm == "pm" and hour != 12:
            hour += 12
        elif am_pm == "am" and hour == 12:
            hour = 0
        
        time_value = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
        return time_value, 0.95
    
    def _parse_24hour(self, match) -> Tuple[datetime, float]:
        hour = int(match.group(1))
        minute = int(match.group(2))
        
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            time_value = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
            return time_value, 0.95
        return None, 0.0
    
    def _parse_hour_only(self, match) -> Tuple[datetime, float]:
        hour = int(match.group(1))
        am_pm = match.group(2).lower()
        
        if am_pm == "pm" and hour != 12:
            hour += 12
        elif am_pm == "am" and hour == 12:
            hour = 0
        
        time_value = datetime.now().replace(hour=hour, minute=0, second=0, microsecond=0)
        return time_value, 0.85
    
    def _parse_time_of_day(self, match) -> Tuple[datetime, float]:
        time_of_day = match.group(1).lower()
        time_map = {
            "morning": (9, 0),
            "afternoon": (14, 0),
            "evening": (18, 0),
            "noon": (12, 0),
            "midnight": (0, 0),
        }
        
        if time_of_day in time_map:
            hour, minute = time_map[time_of_day]
            time_value = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
            return time_value, 0.75
        return None, 0.0
    
    def _is_valid_name(self, name: str) -> bool:
        if not name or len(name) < 2:
            return False
        
        if len(name) > 50:
            return False
        
        if not re.match(r"^[A-Za-z\s\-']+$", name):
            return False
        
        return True
    
    def extract_all_slots(self, text: str, slot_types: list[str]) -> Dict[str, ExtractedSlot]:
        extracted = {}
        
        for slot_type in slot_types:
            if slot_type == "date":
                slot = self.extract_date(text)
                if slot:
                    extracted[slot_type] = slot
            elif slot_type == "time":
                slot = self.extract_time(text)
                if slot:
                    extracted[slot_type] = slot
            elif slot_type == "name":
                slot = self.extract_name(text)
                if slot:
                    extracted[slot_type] = slot
        
        return extracted

