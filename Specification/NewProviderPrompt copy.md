Workflow:
	1.	Provider extrahiert Adresse
	2.	Webservice prüft: Koordinaten vorhanden?
	3.	Falls nein → geocode()
	4.	Koordinaten im Event speichern
	5.	App bekommt nur Lat/Lon

👉 Die App selbst macht kein Geocoding.


location = geolocator.geocode({
    "street": "Sophienstraße 18",
    "city": "Berlin",
    "postcode": "10178",
    "country": "Germany"
})

geopy + Nominatim (OpenStreetMap)


Nominatim verlangt:
	•	eindeutigen user_agent
	•	keine Massenabfragen
	•	idealerweise Caching

👉 Für dein System:
	•	Geocoding nur beim ersten Auftreten eines Veranstaltungsorts
	•	Koordinaten danach persistieren oder cachen
	•	niemals bei jedem Update neu geocodieren