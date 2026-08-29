from django.contrib.gis.geos import LineString, Point
from django.core.management.base import BaseCommand

from listings.models import BoardingHouse, Faculty, RoadSegment

# NOTE: These are placeholder coordinates for demo/testing purposes only.

FACULTIES = [
    {"name": "Teknik Informatika", "address": "Jl. Unima, Tataaran Satu, Kec. Tondano Sel., Kabupaten Minahasa, Sulawesi Utara", "lng": 1.2645261151216165, "lat": 124.88770287316223},
    {"name": "Pendidikan Teknik Informatika", "address": "Jl. Unima, Tataaran Satu, Kec. Tondano Sel., Kabupaten Minahasa, Sulawesi Utara", "lng": 1.2657802515003769, "lat": 124.88718718298111},
    {"name": "Teknik Mesin", "address": "Tataaran Satu, Kec. Tondano Sel., Kabupaten Minahasa, Sulawesi Utara", "lng": 1.2668400535311486, "lat": 124.88616152977424},
    {"name": "Teknik Arsitektur", "address": "Tataaran Satu, Kec. Tondano Sel., Kabupaten Minahasa, Sulawesi Utara", "lng": 1.2660404346465146, "lat": 124.88805031842583},
]

BOARDING_HOUSES = [
    {
        "name": "Kost Vegaly", "price_min": 350000, "price_max": 500000, "room_type": "campur",
        "facilities": ["wifi", "kamar_mandi_dalam"], "lng": 1.2681638000846318, "lat": 124.87652951050738,
        "address": "Tataaran Patar, Kec. Tondano Sel., Kabupaten Minahasa, Sulawesi Utara", "contact": "0812-0000-0001",
    },
    {
        "name": "Sakura House", "price_min": 500000, "price_max": 800000, "room_type": "campur",
        "facilities": ["wifi", "parkir", "kamar_mandi_dalam"], "lng": 1.2664309429429765, "lat": 124.87498434847735,
        "address": "Tataaran Patar, Kec. Tondano Sel., Kabupaten Minahasa, Sulawesi Utara", "contact": "0812-0000-0002",
    },
    {
        "name": "Kost Gloria", "price_min": 350000, "price_max": 500000, "room_type": "campur",
        "facilities": ["wifi", "ac", "kamar_mandi_dalam", "laundry"], "lng": 1.26712905083638, "lat": 124.87574270106187,
        "address": "perum unima Kel maesa, Tataaran Patar, Kec. Tondano Sel., Kabupaten Minahasa, Sulawesi Utara", "contact": "0812-0000-0003",
    },
]

ROAD_SEGMENTS = [
    
]


class Command(BaseCommand):
    help = "Seed the database with sample faculties, boarding houses, and road segments."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush", action="store_true",
            help="Delete existing rows in these tables before seeding.",
        )

    def handle(self, *args, **options):
        if options["flush"]:
            self.stdout.write("Flushing existing data...")
            BoardingHouse.objects.all().delete()
            Faculty.objects.all().delete()
            RoadSegment.objects.all().delete()

        self.stdout.write("Seeding faculties...")
        for f in FACULTIES:
            Faculty.objects.get_or_create(
                name=f["name"],
                defaults={"address": f["address"], "geom": Point(f["lng"], f["lat"], srid=4326)},
            )

        self.stdout.write("Seeding boarding houses...")
        for b in BOARDING_HOUSES:
            BoardingHouse.objects.get_or_create(
                name=b["name"],
                defaults={
                    "address": b["address"],
                    "price_min": b["price_min"],
                    "price_max": b["price_max"],
                    "room_type": b["room_type"],
                    "facilities": b["facilities"],
                    "contact": b["contact"],
                    "geom": Point(b["lng"], b["lat"], srid=4326),
                },
            )

        self.stdout.write("Seeding road segments...")
        for r in ROAD_SEGMENTS:
            RoadSegment.objects.get_or_create(
                name=r["name"],
                defaults={
                    "condition": r["condition"],
                    "notes": r.get("notes", ""),
                    "geom": LineString([(p[0], p[1]) for p in r["points"]], srid=4326),
                },
            )

        self.stdout.write(self.style.SUCCESS("Seed complete."))
