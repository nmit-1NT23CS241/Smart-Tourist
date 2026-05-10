from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import random
from collections import deque

app = FastAPI(title="SafarAI RL API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

DESTINATIONS = [
    # ANDAMAN & NICOBAR
    {"id":0,"name":"Havelock Island","state":"Andaman & Nicobar","tags":["beach","nature"],"budget":15000,"sustainability":0.88,"crowd":0.25,"description":"Famous for Radhanagar Beach, pristine coral reefs, snorkeling and scuba diving paradise"},
    {"id":1,"name":"Neil Island","state":"Andaman & Nicobar","tags":["beach","nature"],"budget":13000,"sustainability":0.9,"crowd":0.15,"description":"Quiet island with natural rock formations, Laxmanpur and Bharatpur beaches"},
    {"id":2,"name":"Port Blair","state":"Andaman & Nicobar","tags":["heritage","culture"],"budget":12000,"sustainability":0.65,"crowd":0.5,"description":"Capital of Andaman, gateway to islands with museums and colonial history"},
    {"id":3,"name":"Radhanagar Beach","state":"Andaman & Nicobar","tags":["beach","nature"],"budget":14000,"sustainability":0.9,"crowd":0.2,"description":"Rated one of Asia's best beaches with crystal clear turquoise water and white sand"},
    {"id":4,"name":"Cellular Jail","state":"Andaman & Nicobar","tags":["heritage"],"budget":12000,"sustainability":0.7,"crowd":0.45,"description":"Historic colonial prison known as Kala Pani, powerful sound and light show every evening"},
    {"id":5,"name":"Baratang Island","state":"Andaman & Nicobar","tags":["nature"],"budget":13000,"sustainability":0.88,"crowd":0.15,"description":"Unique limestone caves, mud volcanoes and dense mangrove creeks reachable by boat"},
    {"id":6,"name":"Elephant Beach","state":"Andaman & Nicobar","tags":["beach","nature"],"budget":13000,"sustainability":0.85,"crowd":0.2,"description":"Best snorkeling spot in Andaman with vibrant coral reefs and marine life"},
    {"id":7,"name":"Ross Island","state":"Andaman & Nicobar","tags":["heritage","nature"],"budget":12000,"sustainability":0.75,"crowd":0.3,"description":"Former British administrative headquarters now overtaken by nature and deer"},

    # ANDHRA PRADESH
    {"id":8,"name":"Tirupati","state":"Andhra Pradesh","tags":["culture","heritage"],"budget":3000,"sustainability":0.55,"crowd":0.95,"description":"One of the most visited religious sites in the world, home to Lord Venkateswara temple"},
    {"id":9,"name":"Araku Valley","state":"Andhra Pradesh","tags":["nature","culture"],"budget":3000,"sustainability":0.85,"crowd":0.25,"description":"Scenic valley with coffee plantations, tribal culture and the famous Borra Caves nearby"},
    {"id":10,"name":"Visakhapatnam","state":"Andhra Pradesh","tags":["beach","culture"],"budget":4000,"sustainability":0.6,"crowd":0.7,"description":"City of destiny with beautiful beaches, submarine museum and Araku Valley access"},
    {"id":11,"name":"Borra Caves","state":"Andhra Pradesh","tags":["nature"],"budget":3000,"sustainability":0.8,"crowd":0.3,"description":"Million year old stalactite and stalagmite caves in the Eastern Ghats"},
    {"id":12,"name":"Gandikota","state":"Andhra Pradesh","tags":["heritage","nature"],"budget":2500,"sustainability":0.85,"crowd":0.15,"description":"Grand Canyon of India, a stunning gorge carved by Penna river with a 12th century fort"},

    # ARUNACHAL PRADESH
    {"id":13,"name":"Tawang","state":"Arunachal Pradesh","tags":["culture","nature"],"budget":8000,"sustainability":0.88,"crowd":0.2,"description":"Home to one of the largest Buddhist monasteries in Asia, stunning Himalayan landscapes"},
    {"id":14,"name":"Ziro Valley","state":"Arunachal Pradesh","tags":["nature","culture"],"budget":7000,"sustainability":0.92,"crowd":0.1,"description":"UNESCO World Heritage nominee with Apatani tribal culture and lush pine forests"},
    {"id":15,"name":"Namdapha National Park","state":"Arunachal Pradesh","tags":["nature"],"budget":8000,"sustainability":0.95,"crowd":0.05,"description":"Largest protected area in Eastern Himalayas, home to snow leopard and clouded leopard"},
    {"id":16,"name":"Sela Pass","state":"Arunachal Pradesh","tags":["nature"],"budget":8000,"sustainability":0.9,"crowd":0.15,"description":"High altitude mountain pass at 13,700 ft with a sacred lake and snow-capped peaks"},

    # ASSAM
    {"id":17,"name":"Kaziranga National Park","state":"Assam","tags":["nature"],"budget":6000,"sustainability":0.9,"crowd":0.25,"description":"UNESCO site housing 2/3 of world's one-horned rhinoceros, tiger reserve and elephant rides"},
    {"id":18,"name":"Majuli","state":"Assam","tags":["culture","nature"],"budget":4000,"sustainability":0.88,"crowd":0.15,"description":"World's largest river island, center of Vaishnavite culture with ancient satras"},
    {"id":19,"name":"Kamakhya Temple","state":"Assam","tags":["culture","heritage"],"budget":3500,"sustainability":0.55,"crowd":0.8,"description":"One of the most powerful Shakti temples, located atop Nilachal Hill in Guwahati"},
    {"id":20,"name":"Manas National Park","state":"Assam","tags":["nature"],"budget":5500,"sustainability":0.9,"crowd":0.15,"description":"UNESCO World Heritage Site at the foothills of Bhutan, home to golden langur and pygmy hog"},

    # BIHAR
    {"id":21,"name":"Bodh Gaya","state":"Bihar","tags":["heritage","culture"],"budget":3000,"sustainability":0.65,"crowd":0.6,"description":"Where Gautama Buddha attained enlightenment under the sacred Bodhi Tree, UNESCO site"},
    {"id":22,"name":"Nalanda","state":"Bihar","tags":["heritage"],"budget":2500,"sustainability":0.7,"crowd":0.4,"description":"Ruins of the world's oldest university from 5th century AD, UNESCO World Heritage Site"},
    {"id":23,"name":"Rajgir","state":"Bihar","tags":["heritage","culture"],"budget":2500,"sustainability":0.7,"crowd":0.35,"description":"Ancient city significant for both Buddhism and Jainism with hot springs and Griddhakuta Hill"},

    # CHANDIGARH
    {"id":24,"name":"Rock Garden Chandigarh","state":"Chandigarh","tags":["culture"],"budget":2000,"sustainability":0.7,"crowd":0.6,"description":"Unique sculpture garden made entirely from industrial and urban waste by Nek Chand"},
    {"id":25,"name":"Sukhna Lake","state":"Chandigarh","tags":["nature"],"budget":1500,"sustainability":0.75,"crowd":0.55,"description":"Serene reservoir at the foothills of Shivaliks, perfect for boating and morning walks"},

    # CHHATTISGARH
    {"id":26,"name":"Chitrakote Falls","state":"Chhattisgarh","tags":["nature"],"budget":3000,"sustainability":0.88,"crowd":0.25,"description":"Widest waterfall in India, often called the Niagara of India on the Indravati River"},
    {"id":27,"name":"Bastar","state":"Chhattisgarh","tags":["culture","nature"],"budget":3500,"sustainability":0.9,"crowd":0.1,"description":"Rich tribal culture, dense forests, unique Bastar Dussehra festival lasting 75 days"},
    {"id":28,"name":"Kanger Valley National Park","state":"Chhattisgarh","tags":["nature"],"budget":3000,"sustainability":0.92,"crowd":0.1,"description":"Biosphere reserve with Kutumsar caves, Tirathgarh falls and rare blind fish species"},

    # DELHI
    {"id":29,"name":"India Gate","state":"Delhi","tags":["heritage","culture"],"budget":3000,"sustainability":0.5,"crowd":0.85,"description":"War memorial for 70,000 soldiers of British Indian Army, iconic landmark on Rajpath"},
    {"id":30,"name":"Red Fort","state":"Delhi","tags":["heritage"],"budget":3000,"sustainability":0.55,"crowd":0.8,"description":"Magnificent Mughal fort built by Shah Jahan, UNESCO World Heritage Site"},
    {"id":31,"name":"Qutub Minar","state":"Delhi","tags":["heritage"],"budget":2500,"sustainability":0.6,"crowd":0.75,"description":"Tallest brick minaret in the world, UNESCO site built in 1193 by Qutub ud-Din Aibak"},
    {"id":32,"name":"Humayun's Tomb","state":"Delhi","tags":["heritage"],"budget":2500,"sustainability":0.65,"crowd":0.6,"description":"First garden-tomb on the Indian subcontinent, inspiration for the Taj Mahal"},
    {"id":33,"name":"Lotus Temple","state":"Delhi","tags":["culture","heritage"],"budget":2000,"sustainability":0.7,"crowd":0.65,"description":"Bahai House of Worship shaped like a lotus flower, open to people of all religions"},
    {"id":34,"name":"Akshardham Temple Delhi","state":"Delhi","tags":["culture","heritage"],"budget":2500,"sustainability":0.6,"crowd":0.8,"description":"Stunning modern temple complex showcasing India's art, culture and spirituality"},
    {"id":35,"name":"Chandni Chowk","state":"Delhi","tags":["culture"],"budget":2000,"sustainability":0.4,"crowd":0.9,"description":"One of the oldest and busiest markets in India, famous for street food and wholesale shops"},
    {"id":36,"name":"Hauz Khas Village","state":"Delhi","tags":["culture","heritage"],"budget":2500,"sustainability":0.55,"crowd":0.7,"description":"Medieval water tank complex with ruins, surrounded by trendy cafes and art galleries"},

    # GOA
    {"id":37,"name":"Baga Beach","state":"Goa","tags":["beach","culture"],"budget":6000,"sustainability":0.4,"crowd":0.95,"description":"Famous for nightlife, water sports, beach shacks and the vibrant Tito's Lane"},
    {"id":38,"name":"Calangute Beach","state":"Goa","tags":["beach"],"budget":5500,"sustainability":0.4,"crowd":0.9,"description":"Queen of beaches in Goa, very popular with domestic tourists, lined with shacks"},
    {"id":39,"name":"Anjuna Beach","state":"Goa","tags":["beach","culture"],"budget":5000,"sustainability":0.5,"crowd":0.7,"description":"Known for its famous flea market, trance parties and scenic rocky cliffs"},
    {"id":40,"name":"Palolem Beach","state":"Goa","tags":["beach","nature"],"budget":4500,"sustainability":0.65,"crowd":0.5,"description":"Crescent shaped paradise beach with calm waters, perfect for swimming and kayaking"},
    {"id":41,"name":"Agonda Beach","state":"Goa","tags":["beach","nature"],"budget":4000,"sustainability":0.8,"crowd":0.3,"description":"Pristine secluded beach, nesting site for Olive Ridley turtles, no loud music allowed"},
    {"id":42,"name":"Vagator Beach","state":"Goa","tags":["beach","culture"],"budget":5000,"sustainability":0.55,"crowd":0.6,"description":"Dramatic red cliffs with Chapora Fort view, popular with backpackers and hippies"},
    {"id":43,"name":"Dudhsagar Falls","state":"Goa","tags":["nature"],"budget":4000,"sustainability":0.85,"crowd":0.45,"description":"Spectacular four-tiered milky white waterfall on the Goa-Karnataka border"},
    {"id":44,"name":"Fort Aguada","state":"Goa","tags":["heritage"],"budget":3500,"sustainability":0.7,"crowd":0.55,"description":"17th century Portuguese fort at the confluence of Mandovi river and Arabian Sea"},
    {"id":45,"name":"Old Goa Churches","state":"Goa","tags":["heritage","culture"],"budget":3000,"sustainability":0.7,"crowd":0.6,"description":"UNESCO World Heritage churches including Basilica of Bom Jesus with St Francis Xavier's remains"},
    {"id":46,"name":"Butterfly Beach","state":"Goa","tags":["beach","nature"],"budget":4500,"sustainability":0.85,"crowd":0.15,"description":"Only accessible by boat, hidden gem surrounded by dense forest, shaped like a butterfly"},
    {"id":47,"name":"Morjim Beach","state":"Goa","tags":["beach","nature"],"budget":4500,"sustainability":0.75,"crowd":0.25,"description":"Turtle beach in North Goa, quieter atmosphere, popular with Russian tourists"},
    {"id":48,"name":"Panaji","state":"Goa","tags":["culture","heritage"],"budget":4000,"sustainability":0.6,"crowd":0.6,"description":"Charming capital city with Portuguese-era houses, Fontainhas Latin Quarter and Mandovi River"},

    # GUJARAT
    {"id":49,"name":"Statue of Unity","state":"Gujarat","tags":["heritage","culture"],"budget":5000,"sustainability":0.6,"crowd":0.7,"description":"World's tallest statue at 182m, tribute to Sardar Vallabhbhai Patel in Narmada district"},
    {"id":50,"name":"Rann of Kutch","state":"Gujarat","tags":["nature","culture"],"budget":5000,"sustainability":0.8,"crowd":0.35,"description":"World's largest salt desert, magical under full moon during Rann Utsav festival"},
    {"id":51,"name":"Gir National Park","state":"Gujarat","tags":["nature"],"budget":6000,"sustainability":0.88,"crowd":0.3,"description":"Only home of Asiatic Lions in the world, also has leopards and over 300 bird species"},
    {"id":52,"name":"Dwarka","state":"Gujarat","tags":["culture","heritage"],"budget":3500,"sustainability":0.6,"crowd":0.75,"description":"One of the Char Dham pilgrimage sites, ancient city associated with Lord Krishna"},
    {"id":53,"name":"Somnath Temple","state":"Gujarat","tags":["heritage","culture"],"budget":3500,"sustainability":0.55,"crowd":0.8,"description":"First of the twelve Jyotirlinga shrines of Lord Shiva, on the shores of Arabian Sea"},
    {"id":54,"name":"Mandvi Beach","state":"Gujarat","tags":["beach","heritage"],"budget":3500,"sustainability":0.75,"crowd":0.25,"description":"Clean beach with working shipyard, summer palace of Kutch royals nearby"},
    {"id":55,"name":"Modhera Sun Temple","state":"Gujarat","tags":["heritage"],"budget":3000,"sustainability":0.75,"crowd":0.3,"description":"11th century sun temple with intricate carvings, hosts Modhera Dance Festival"},

    # HIMACHAL PRADESH
    {"id":56,"name":"Manali","state":"Himachal Pradesh","tags":["nature","culture"],"budget":7000,"sustainability":0.7,"crowd":0.8,"description":"Snow peaks, Rohtang Pass, Solang Valley, adventure sports and Old Manali cafes"},
    {"id":57,"name":"Shimla","state":"Himachal Pradesh","tags":["nature","heritage"],"budget":6000,"sustainability":0.7,"crowd":0.75,"description":"Former summer capital of British India, toy train, Mall Road and colonial architecture"},
    {"id":58,"name":"Kasol","state":"Himachal Pradesh","tags":["nature"],"budget":4000,"sustainability":0.75,"crowd":0.45,"description":"Mini Israel of India in Parvati Valley, backpacker haven with riverside camping"},
    {"id":59,"name":"Spiti Valley","state":"Himachal Pradesh","tags":["nature","culture"],"budget":8000,"sustainability":0.95,"crowd":0.1,"description":"Remote cold desert with ancient monasteries Key and Tabo, dramatic landscapes and starry skies"},
    {"id":60,"name":"Dharamshala","state":"Himachal Pradesh","tags":["culture","nature"],"budget":5000,"sustainability":0.8,"crowd":0.5,"description":"Home of Dalai Lama, Tibetan culture, trekking trails and stunning Dhauladhar ranges"},
    {"id":61,"name":"Bir Billing","state":"Himachal Pradesh","tags":["nature"],"budget":5000,"sustainability":0.85,"crowd":0.25,"description":"World's second best paragliding site, landing site is in Bir, take-off from Billing"},
    {"id":62,"name":"Khajjiar","state":"Himachal Pradesh","tags":["nature"],"budget":4000,"sustainability":0.85,"crowd":0.35,"description":"Mini Switzerland of India, circular lake surrounded by dense deodar forests"},
    {"id":63,"name":"Dalhousie","state":"Himachal Pradesh","tags":["nature","heritage"],"budget":4500,"sustainability":0.8,"crowd":0.4,"description":"Colonial hill station with Scottish and Victorian architecture, Kalatop Wildlife Sanctuary"},

    # JAMMU & KASHMIR
    {"id":64,"name":"Srinagar","state":"Jammu & Kashmir","tags":["nature","culture"],"budget":7000,"sustainability":0.75,"crowd":0.6,"description":"Dal Lake houseboats, Mughal gardens, Hazratbal Shrine and famous Kashmiri handicrafts"},
    {"id":65,"name":"Gulmarg","state":"Jammu & Kashmir","tags":["nature"],"budget":9000,"sustainability":0.8,"crowd":0.55,"description":"Asia's highest gondola, world-class skiing in winter, meadows of flowers in summer"},
    {"id":66,"name":"Pahalgam","state":"Jammu & Kashmir","tags":["nature"],"budget":7000,"sustainability":0.82,"crowd":0.5,"description":"Valley of Shepherds, base for Amarnath Yatra, Lidder river and Betaab Valley"},
    {"id":67,"name":"Sonamarg","state":"Jammu & Kashmir","tags":["nature"],"budget":7000,"sustainability":0.85,"crowd":0.4,"description":"Meadow of Gold, gateway to Thajiwas Glacier, stunning alpine meadows"},
    {"id":68,"name":"Dal Lake","state":"Jammu & Kashmir","tags":["nature","culture"],"budget":6000,"sustainability":0.65,"crowd":0.7,"description":"Jewel in the crown of Kashmir, famous for houseboats, shikara rides and floating gardens"},
    {"id":69,"name":"Vaishno Devi","state":"Jammu & Kashmir","tags":["culture","heritage"],"budget":4000,"sustainability":0.55,"crowd":0.9,"description":"One of the most visited Hindu shrines in India, trekking through Trikuta Mountains"},

    # JHARKHAND
    {"id":70,"name":"Netarhat","state":"Jharkhand","tags":["nature"],"budget":3000,"sustainability":0.88,"crowd":0.15,"description":"Queen of Chotanagpur Plateau, famous for sunrise and sunset views, dense forests"},
    {"id":71,"name":"Betla National Park","state":"Jharkhand","tags":["nature"],"budget":4000,"sustainability":0.88,"crowd":0.15,"description":"One of the first tiger reserves in India with elephants, leopards and sloth bears"},
    {"id":72,"name":"Hundru Falls","state":"Jharkhand","tags":["nature"],"budget":2500,"sustainability":0.85,"crowd":0.3,"description":"Stunning waterfall on Subarnarekha River, 98 meters high, perfect picnic spot"},

    # KARNATAKA
    {"id":73,"name":"Coorg Coffee Estates","state":"Karnataka","tags":["nature","culture"],"budget":3000,"sustainability":0.9,"crowd":0.3,"description":"Misty hills covered with coffee and spice plantations, Kodava tribal culture"},
    {"id":74,"name":"Hampi","state":"Karnataka","tags":["heritage"],"budget":2500,"sustainability":0.8,"crowd":0.4,"description":"UNESCO World Heritage ruins of Vijayanagara Empire with 500+ ancient monuments"},
    {"id":75,"name":"Mysuru Palace","state":"Karnataka","tags":["heritage","culture"],"budget":2000,"sustainability":0.7,"crowd":0.75,"description":"Magnificent Indo-Saracenic palace, illuminated on Sundays, venue for Dasara celebrations"},
    {"id":76,"name":"Chikmagalur Hills","state":"Karnataka","tags":["nature"],"budget":2800,"sustainability":0.9,"crowd":0.2,"description":"Birthplace of coffee in India, misty peaks, Mullayanagiri highest peak in Karnataka"},
    {"id":77,"name":"Gokarna Beach","state":"Karnataka","tags":["beach","culture"],"budget":2500,"sustainability":0.8,"crowd":0.3,"description":"Sacred temple town with pristine Om Beach and Half Moon Beach"},
    {"id":78,"name":"Badami Caves","state":"Karnataka","tags":["heritage"],"budget":2500,"sustainability":0.85,"crowd":0.2,"description":"6th century Chalukya rock-cut cave temples with stunning sculptures and Agastya Lake"},
    {"id":79,"name":"Jog Falls","state":"Karnataka","tags":["nature"],"budget":2500,"sustainability":0.85,"crowd":0.4,"description":"Second highest plunge waterfall in India on Sharavathi River, spectacular in monsoon"},
    {"id":80,"name":"Dandeli","state":"Karnataka","tags":["nature"],"budget":3500,"sustainability":0.9,"crowd":0.2,"description":"White water rafting and wildlife safari in Kali Tiger Reserve, kayaking and jungle camps"},
    {"id":81,"name":"Kabini","state":"Karnataka","tags":["nature"],"budget":8000,"sustainability":0.88,"crowd":0.2,"description":"Famous for elephant gatherings, black panther sightings and luxury forest lodges"},
    {"id":82,"name":"Sakleshpur","state":"Karnataka","tags":["nature"],"budget":2500,"sustainability":0.88,"crowd":0.15,"description":"Coffee and pepper plantation trails, railway trekking and misty Western Ghats"},

    # KERALA
    {"id":83,"name":"Alleppey Backwaters","state":"Kerala","tags":["nature","culture"],"budget":5000,"sustainability":0.8,"crowd":0.5,"description":"Houseboat rides through scenic canal networks, paddy fields and coconut groves"},
    {"id":84,"name":"Munnar Tea Gardens","state":"Kerala","tags":["nature"],"budget":4000,"sustainability":0.85,"crowd":0.5,"description":"Lush green tea plantations at 1600m altitude, Eravikulam National Park and Anamudi peak"},
    {"id":85,"name":"Varkala Cliff Beach","state":"Kerala","tags":["beach","culture"],"budget":3500,"sustainability":0.75,"crowd":0.4,"description":"Dramatic cliffside beach with natural mineral springs, yoga retreats and Janardhana temple"},
    {"id":86,"name":"Wayanad","state":"Kerala","tags":["nature"],"budget":3200,"sustainability":0.88,"crowd":0.3,"description":"Dense forests with elephants, tigers, Edakkal caves with prehistoric carvings"},
    {"id":87,"name":"Thekkady Periyar","state":"Kerala","tags":["nature"],"budget":4500,"sustainability":0.9,"crowd":0.35,"description":"Tiger reserve with boat safari on Periyar Lake, spice plantations and bamboo rafting"},
    {"id":88,"name":"Kochi Fort Area","state":"Kerala","tags":["heritage","culture"],"budget":3500,"sustainability":0.65,"crowd":0.6,"description":"Chinese fishing nets, Jewish synagogue, Dutch Palace and bustling spice markets"},
    {"id":89,"name":"Kovalam Beach","state":"Kerala","tags":["beach"],"budget":4000,"sustainability":0.7,"crowd":0.55,"description":"Crescent shaped lighthouse beach, Hawah Beach popular with international tourists"},
    {"id":90,"name":"Athirappilly Falls","state":"Kerala","tags":["nature"],"budget":3000,"sustainability":0.85,"crowd":0.5,"description":"Largest waterfall in Kerala, called the Niagara of India, filming location of many movies"},
    {"id":91,"name":"Bekal Fort","state":"Kerala","tags":["heritage","beach"],"budget":3000,"sustainability":0.75,"crowd":0.3,"description":"Largest fort in Kerala on the coast, stunning views of the Arabian Sea"},

    # LADAKH
    {"id":92,"name":"Pangong Lake","state":"Ladakh","tags":["nature"],"budget":10000,"sustainability":0.88,"crowd":0.3,"description":"Stunning high altitude lake at 14,270 ft, changes color from blue to green to red"},
    {"id":93,"name":"Leh City","state":"Ladakh","tags":["culture","heritage"],"budget":9000,"sustainability":0.8,"crowd":0.45,"description":"Leh Palace, Shanti Stupa, bustling market and gateway to Ladakh's adventures"},
    {"id":94,"name":"Nubra Valley","state":"Ladakh","tags":["nature","culture"],"budget":10000,"sustainability":0.88,"crowd":0.2,"description":"Bactrian double-humped camels in sand dunes, Diskit Monastery and Hunder village"},
    {"id":95,"name":"Magnetic Hill","state":"Ladakh","tags":["nature"],"budget":9000,"sustainability":0.85,"crowd":0.35,"description":"Gravity defying hill where vehicles appear to move uphill, optical illusion phenomenon"},
    {"id":96,"name":"Tso Moriri","state":"Ladakh","tags":["nature"],"budget":10000,"sustainability":0.92,"crowd":0.1,"description":"Remote high altitude lake at 15,075 ft, breeding ground for bar-headed geese"},
    {"id":97,"name":"Zanskar Valley","state":"Ladakh","tags":["nature","culture"],"budget":11000,"sustainability":0.93,"crowd":0.08,"description":"Remote valley famous for Chadar Trek on frozen Zanskar River in winter"},

    # LAKSHADWEEP
    {"id":98,"name":"Agatti Island","state":"Lakshadweep","tags":["beach","nature"],"budget":20000,"sustainability":0.9,"crowd":0.1,"description":"Gateway island with a lagoon of crystal clear water, coral reefs and water sports"},
    {"id":99,"name":"Bangaram Island","state":"Lakshadweep","tags":["beach","nature"],"budget":25000,"sustainability":0.92,"crowd":0.08,"description":"Uninhabited coral atoll with pristine beaches, excellent for snorkeling and diving"},
    {"id":100,"name":"Minicoy Island","state":"Lakshadweep","tags":["beach","culture"],"budget":20000,"sustainability":0.88,"crowd":0.1,"description":"Southernmost island with unique Mahl culture, lighthouse and tuna fishing tradition"},

    # MADHYA PRADESH
    {"id":101,"name":"Khajuraho Temples","state":"Madhya Pradesh","tags":["heritage"],"budget":4500,"sustainability":0.7,"crowd":0.45,"description":"UNESCO temples famous for intricate erotic sculptures depicting ancient Kamasutra"},
    {"id":102,"name":"Kanha National Park","state":"Madhya Pradesh","tags":["nature"],"budget":8000,"sustainability":0.88,"crowd":0.35,"description":"Inspiration for Jungle Book, excellent tiger sightings and beautiful meadows"},
    {"id":103,"name":"Bandhavgarh National Park","state":"Madhya Pradesh","tags":["nature"],"budget":8000,"sustainability":0.88,"crowd":0.3,"description":"Highest density of tigers in any national park in the world"},
    {"id":104,"name":"Pachmarhi","state":"Madhya Pradesh","tags":["nature"],"budget":4000,"sustainability":0.85,"crowd":0.3,"description":"Only hill station in MP with Bee Falls, Pandava Caves and Jata Shankar temple"},
    {"id":105,"name":"Orchha","state":"Madhya Pradesh","tags":["heritage"],"budget":3500,"sustainability":0.78,"crowd":0.3,"description":"Medieval town with cenotaphs, palaces and Ram Raja temple on Betwa River"},
    {"id":106,"name":"Sanchi Stupa","state":"Madhya Pradesh","tags":["heritage"],"budget":3000,"sustainability":0.75,"crowd":0.35,"description":"UNESCO World Heritage Buddhist monument from 3rd century BC commissioned by Emperor Ashoka"},

    # MAHARASHTRA
    {"id":107,"name":"Ajanta Caves","state":"Maharashtra","tags":["heritage"],"budget":4000,"sustainability":0.75,"crowd":0.5,"description":"UNESCO Buddhist cave paintings and sculptures from 2nd century BC to 5th century AD"},
    {"id":108,"name":"Ellora Caves","state":"Maharashtra","tags":["heritage"],"budget":4000,"sustainability":0.75,"crowd":0.5,"description":"UNESCO rock-cut temples of Hindu, Buddhist and Jain religions, Kailasa temple is a marvel"},
    {"id":109,"name":"Lonavala","state":"Maharashtra","tags":["nature"],"budget":3000,"sustainability":0.7,"crowd":0.75,"description":"Popular hill station near Pune with Bhushi Dam, Karla Caves and famous chikki"},
    {"id":110,"name":"Mahabaleshwar","state":"Maharashtra","tags":["nature"],"budget":4000,"sustainability":0.75,"crowd":0.7,"description":"Strawberry capital of India, Venna Lake, Arthur's Seat point and beautiful valleys"},
    {"id":111,"name":"Tarkarli Beach","state":"Maharashtra","tags":["beach","nature"],"budget":3500,"sustainability":0.8,"crowd":0.2,"description":"Crystal clear water at confluence of Karli river and sea, scuba diving and snorkeling"},
    {"id":112,"name":"Tadoba National Park","state":"Maharashtra","tags":["nature"],"budget":7000,"sustainability":0.88,"crowd":0.25,"description":"Maharashtra's oldest national park, excellent tiger sightings and dry deciduous forests"},
    {"id":113,"name":"Mumbai","state":"Maharashtra","tags":["culture","heritage"],"budget":6000,"sustainability":0.45,"crowd":0.95,"description":"City of dreams with Gateway of India, Marine Drive, Elephanta Caves and street food"},

    # MANIPUR
    {"id":114,"name":"Loktak Lake","state":"Manipur","tags":["nature","culture"],"budget":4000,"sustainability":0.85,"crowd":0.15,"description":"Largest freshwater lake in Northeast India with floating phumdis and Keibul Lamjao NP"},
    {"id":115,"name":"Imphal","state":"Manipur","tags":["culture","heritage"],"budget":3500,"sustainability":0.65,"crowd":0.4,"description":"Kangla Fort, Ima Keithel women's market, WWII cemeteries and Manipuri dance"},

    # MEGHALAYA
    {"id":116,"name":"Shillong","state":"Meghalaya","tags":["nature","culture"],"budget":5000,"sustainability":0.8,"crowd":0.55,"description":"Scotland of the East, Ward's Lake, Don Bosco Museum and amazing live music culture"},
    {"id":117,"name":"Cherrapunji","state":"Meghalaya","tags":["nature"],"budget":5000,"sustainability":0.88,"crowd":0.3,"description":"One of wettest places on earth, Nohkalikai Falls, Mawsmai Caves and living root bridges"},
    {"id":118,"name":"Dawki","state":"Meghalaya","tags":["nature"],"budget":4500,"sustainability":0.9,"crowd":0.2,"description":"Crystal clear Umngot River where boats appear to float in air, on Bangladesh border"},
    {"id":119,"name":"Living Root Bridges","state":"Meghalaya","tags":["nature","culture"],"budget":5000,"sustainability":0.95,"crowd":0.2,"description":"Ancient bioengineering by Khasi tribe, double decker root bridge near Nongriat village"},
    {"id":120,"name":"Mawlynnong","state":"Meghalaya","tags":["culture","nature"],"budget":4500,"sustainability":0.95,"crowd":0.15,"description":"Cleanest village in Asia award winner, eco tourism, bamboo tree houses and root bridges"},

    # MIZORAM
    {"id":121,"name":"Aizawl","state":"Mizoram","tags":["culture"],"budget":5000,"sustainability":0.75,"crowd":0.3,"description":"Capital city built on steep hillside, Mizoram State Museum and Solomon's Temple"},
    {"id":122,"name":"Phawngpui Hills","state":"Mizoram","tags":["nature"],"budget":6000,"sustainability":0.92,"crowd":0.05,"description":"Blue Mountain, highest peak in Mizoram with rhododendrons and rare orchids"},

    # NAGALAND
    {"id":123,"name":"Kohima","state":"Nagaland","tags":["heritage","culture"],"budget":5000,"sustainability":0.75,"crowd":0.3,"description":"WWII battlefield, Kohima War Cemetery, Naga Heritage Village and Dzukou Valley access"},
    {"id":124,"name":"Dzukou Valley","state":"Nagaland","tags":["nature"],"budget":5000,"sustainability":0.93,"crowd":0.1,"description":"Valley of flowers at the border of Nagaland and Manipur, lily flowers bloom in July"},
    {"id":125,"name":"Hornbill Festival","state":"Nagaland","tags":["culture"],"budget":5500,"sustainability":0.8,"crowd":0.6,"description":"Festival of festivals showcasing all Naga tribes, held in December at Kisama village"},

    # ODISHA
    {"id":126,"name":"Konark Sun Temple","state":"Odisha","tags":["heritage"],"budget":3500,"sustainability":0.75,"crowd":0.45,"description":"UNESCO 13th century chariot-shaped temple with 24 intricately carved wheels"},
    {"id":127,"name":"Puri Jagannath Temple","state":"Odisha","tags":["culture","heritage"],"budget":3000,"sustainability":0.55,"crowd":0.85,"description":"One of Char Dham pilgrimages, famous Rath Yatra with 45-foot chariots"},
    {"id":128,"name":"Chilika Lake","state":"Odisha","tags":["nature"],"budget":2500,"sustainability":0.85,"crowd":0.3,"description":"Asia's largest brackish lake, migratory birds from Siberia and Irrawaddy dolphins"},
    {"id":129,"name":"Simlipal National Park","state":"Odisha","tags":["nature"],"budget":5000,"sustainability":0.9,"crowd":0.15,"description":"Tiger reserve with waterfalls, sal forests and rare melanistic tigers"},
    {"id":130,"name":"Gopalpur Beach","state":"Odisha","tags":["beach"],"budget":2500,"sustainability":0.7,"crowd":0.35,"description":"Quiet beach town with a colonial past, lighthouse and fresh seafood"},

    # PUDUCHERRY
    {"id":131,"name":"Promenade Beach Pondicherry","state":"Puducherry","tags":["beach","culture"],"budget":3000,"sustainability":0.65,"crowd":0.65,"description":"4km beach promenade with French war memorial, Gandhi statue and evening crowds"},
    {"id":132,"name":"Auroville","state":"Puducherry","tags":["culture"],"budget":3500,"sustainability":0.9,"crowd":0.4,"description":"Experimental universal township with Matrimandir golden sphere, founded by The Mother"},
    {"id":133,"name":"French Colony Pondicherry","state":"Puducherry","tags":["culture","heritage"],"budget":3000,"sustainability":0.7,"crowd":0.6,"description":"Yellow-painted colonial buildings, bougainvillea lanes, cafes and French patisseries"},
    {"id":134,"name":"Paradise Beach Pondicherry","state":"Puducherry","tags":["beach","nature"],"budget":2500,"sustainability":0.8,"crowd":0.3,"description":"Pristine beach accessible only by boat, no vehicles allowed, clean and quiet"},

    # PUNJAB
    {"id":135,"name":"Golden Temple Amritsar","state":"Punjab","tags":["culture","heritage"],"budget":4000,"sustainability":0.6,"crowd":0.9,"description":"Holiest Sikh shrine, free langar for all, stunning reflection in Amrit Sarovar"},
    {"id":136,"name":"Wagah Border","state":"Punjab","tags":["culture"],"budget":3500,"sustainability":0.6,"crowd":0.8,"description":"Daily flag lowering ceremony at India-Pakistan border, patriotic and spectacular"},
    {"id":137,"name":"Anandpur Sahib","state":"Punjab","tags":["culture","heritage"],"budget":3000,"sustainability":0.65,"crowd":0.6,"description":"Important Sikh pilgrimage, birthplace of Khalsa, Virasat-e-Khalsa museum"},

    # RAJASTHAN
    {"id":138,"name":"Jaipur Pink City","state":"Rajasthan","tags":["heritage","culture"],"budget":6000,"sustainability":0.55,"crowd":0.85,"description":"Amber Fort, Hawa Mahal, City Palace, Jantar Mantar and vibrant bazaars"},
    {"id":139,"name":"Udaipur Lake City","state":"Rajasthan","tags":["heritage","culture"],"budget":7000,"sustainability":0.65,"crowd":0.7,"description":"City of lakes, Lake Pichola, City Palace, Sajjangarh and romantic sunsets"},
    {"id":140,"name":"Jaisalmer Golden City","state":"Rajasthan","tags":["heritage","culture"],"budget":6000,"sustainability":0.7,"crowd":0.5,"description":"Living fort city with camel safaris in Thar Desert, havelis and folk music nights"},
    {"id":141,"name":"Jodhpur Blue City","state":"Rajasthan","tags":["heritage","culture"],"budget":5500,"sustainability":0.6,"crowd":0.65,"description":"Mehrangarh Fort towering over blue-painted old city, Jaswant Thada marble cenotaph"},
    {"id":142,"name":"Pushkar","state":"Rajasthan","tags":["culture","heritage"],"budget":3500,"sustainability":0.6,"crowd":0.55,"description":"Sacred lake with 52 ghats, only Brahma temple in world and famous camel fair"},
    {"id":143,"name":"Ranthambore National Park","state":"Rajasthan","tags":["nature"],"budget":8000,"sustainability":0.85,"crowd":0.4,"description":"Best place to spot Bengal tigers, ancient fort inside the park adds to mystique"},
    {"id":144,"name":"Chittorgarh Fort","state":"Rajasthan","tags":["heritage"],"budget":4500,"sustainability":0.7,"crowd":0.3,"description":"Largest fort in India, tales of Rajput valor, Rani Padmini palace and Vijay Stambha"},
    {"id":145,"name":"Sam Sand Dunes","state":"Rajasthan","tags":["nature","culture"],"budget":5000,"sustainability":0.7,"crowd":0.55,"description":"Golden sand dunes of Thar Desert near Jaisalmer, camel rides and cultural evenings"},

    # SIKKIM
    {"id":146,"name":"Gangtok","state":"Sikkim","tags":["culture","nature"],"budget":6000,"sustainability":0.85,"crowd":0.45,"description":"Clean mountain capital with Rumtek Monastery, Nathula Pass and cable car rides"},
    {"id":147,"name":"Tsomgo Lake","state":"Sikkim","tags":["nature"],"budget":6500,"sustainability":0.85,"crowd":0.5,"description":"Sacred glacial lake at 12,313 ft near Nathu La pass, yak rides and stunning scenery"},
    {"id":148,"name":"Yumthang Valley","state":"Sikkim","tags":["nature"],"budget":7000,"sustainability":0.9,"crowd":0.25,"description":"Valley of Flowers of Sikkim, rhododendrons bloom in April, hot springs at Yumthang"},
    {"id":149,"name":"Pelling","state":"Sikkim","tags":["nature","heritage"],"budget":5500,"sustainability":0.88,"crowd":0.3,"description":"Stunning Kanchenjunga views, Pemayangtse Monastery and Rabdentse ruins"},

    # TAMIL NADU
    {"id":150,"name":"Ooty","state":"Tamil Nadu","tags":["nature"],"budget":3000,"sustainability":0.75,"crowd":0.65,"description":"Queen of hill stations in Nilgiris, botanical garden, Ooty Lake and Doddabetta peak"},
    {"id":151,"name":"Kodaikanal","state":"Tamil Nadu","tags":["nature"],"budget":3000,"sustainability":0.8,"crowd":0.45,"description":"Princess of hill stations, star shaped Kodai Lake, Coaker's Walk and Bear Shola Falls"},
    {"id":152,"name":"Madurai Meenakshi Temple","state":"Tamil Nadu","tags":["heritage","culture"],"budget":3000,"sustainability":0.65,"crowd":0.8,"description":"Towering gopurams with 33,000 sculptures, one of India's most magnificent temples"},
    {"id":153,"name":"Mahabalipuram","state":"Tamil Nadu","tags":["heritage","beach"],"budget":3000,"sustainability":0.7,"crowd":0.5,"description":"UNESCO shore temples and rock-cut caves by Bay of Bengal, stone carving tradition"},
    {"id":154,"name":"Rameswaram","state":"Tamil Nadu","tags":["culture","heritage"],"budget":3000,"sustainability":0.6,"crowd":0.75,"description":"Char Dham pilgrimage, Ramanathaswamy temple with longest corridor, Adam's Bridge"},
    {"id":155,"name":"Kanyakumari","state":"Tamil Nadu","tags":["nature","culture"],"budget":3000,"sustainability":0.65,"crowd":0.7,"description":"Southernmost tip of India where three seas meet, Vivekananda Rock Memorial and sunrise"},
    {"id":156,"name":"Thanjavur","state":"Tamil Nadu","tags":["heritage","culture"],"budget":3000,"sustainability":0.7,"crowd":0.45,"description":"Big Temple Brihadeeswara, Tanjore paintings, Carnatic music and Chola art heritage"},
    {"id":157,"name":"Marina Beach Chennai","state":"Tamil Nadu","tags":["beach","culture"],"budget":3500,"sustainability":0.5,"crowd":0.9,"description":"Second longest urban beach in world, lighthouse, ice cream and evening walks"},

    # TELANGANA
    {"id":158,"name":"Hyderabad","state":"Telangana","tags":["culture","heritage"],"budget":4000,"sustainability":0.5,"crowd":0.85,"description":"City of Nizams with Charminar, Golconda Fort, Ramoji Film City and biryani"},
    {"id":159,"name":"Golconda Fort","state":"Telangana","tags":["heritage"],"budget":3500,"sustainability":0.65,"crowd":0.6,"description":"Acoustic marvel where a clap at the entrance is heard at the top, diamond mining history"},
    {"id":160,"name":"Warangal","state":"Telangana","tags":["heritage"],"budget":3000,"sustainability":0.7,"crowd":0.35,"description":"Kakatiya dynasty capital with thousand pillar temple and Warangal Fort"},

    # TRIPURA
    {"id":161,"name":"Neermahal","state":"Tripura","tags":["heritage","nature"],"budget":3000,"sustainability":0.8,"crowd":0.2,"description":"Only water palace in Eastern India built on Rudrasagar Lake, stunning at sunset"},
    {"id":162,"name":"Unakoti","state":"Tripura","tags":["heritage","nature"],"budget":2500,"sustainability":0.82,"crowd":0.15,"description":"Ancient rock carvings of Shiva and other deities in a forest, archaeological marvel"},

    # UTTAR PRADESH
    {"id":163,"name":"Taj Mahal Agra","state":"Uttar Pradesh","tags":["heritage"],"budget":5000,"sustainability":0.5,"crowd":0.95,"description":"One of Seven Wonders, Shah Jahan's monument to love for Mumtaz Mahal, pure white marble"},
    {"id":164,"name":"Varanasi Ghats","state":"Uttar Pradesh","tags":["culture","heritage"],"budget":4000,"sustainability":0.5,"crowd":0.85,"description":"Oldest living city in world, Ganga Aarti ceremony, 88 ghats and boat rides at dawn"},
    {"id":165,"name":"Ayodhya","state":"Uttar Pradesh","tags":["culture","heritage"],"budget":3000,"sustainability":0.55,"crowd":0.85,"description":"Birthplace of Lord Ram, Ram Mandir, Saryu River ghats and religious significance"},
    {"id":166,"name":"Mathura Vrindavan","state":"Uttar Pradesh","tags":["culture","heritage"],"budget":2500,"sustainability":0.55,"crowd":0.8,"description":"Birthplace of Lord Krishna, Banke Bihari temple, Prem Mandir and Holi celebrations"},
    {"id":167,"name":"Lucknow","state":"Uttar Pradesh","tags":["culture","heritage"],"budget":3500,"sustainability":0.55,"crowd":0.7,"description":"City of Nawabs with Bara Imambara, Rumi Darwaza, kebabs and chikankari embroidery"},
    {"id":168,"name":"Prayagraj","state":"Uttar Pradesh","tags":["culture","heritage"],"budget":3000,"sustainability":0.5,"crowd":0.8,"description":"Triveni Sangam, Kumbh Mela venue, Anand Bhawan and Allahabad Fort"},

    # UTTARAKHAND
    {"id":169,"name":"Rishikesh","state":"Uttarakhand","tags":["culture","nature"],"budget":4000,"sustainability":0.75,"crowd":0.7,"description":"Yoga capital of world, Ganga rafting, Laxman Jhula, Beatles Ashram and bungee jumping"},
    {"id":170,"name":"Nainital","state":"Uttarakhand","tags":["nature"],"budget":5000,"sustainability":0.7,"crowd":0.7,"description":"Pear shaped Naini Lake surrounded by hills, boating, snow viewpoint and Mall Road"},
    {"id":171,"name":"Mussoorie","state":"Uttarakhand","tags":["nature"],"budget":5000,"sustainability":0.72,"crowd":0.75,"description":"Queen of Hills, Kempty Falls, Gun Hill, Lal Tibba and Company Garden"},
    {"id":172,"name":"Auli","state":"Uttarakhand","tags":["nature"],"budget":7000,"sustainability":0.85,"crowd":0.3,"description":"Best skiing destination in India with Nanda Devi and Trishul peak views"},
    {"id":173,"name":"Jim Corbett National Park","state":"Uttarakhand","tags":["nature"],"budget":7000,"sustainability":0.85,"crowd":0.35,"description":"Oldest national park in India, best for tiger sightings and elephant safaris"},
    {"id":174,"name":"Valley of Flowers","state":"Uttarakhand","tags":["nature"],"budget":9000,"sustainability":0.95,"crowd":0.2,"description":"UNESCO site with 300+ wildflower species in Himalayan meadow, near Hemkund Sahib"},
    {"id":175,"name":"Kedarnath","state":"Uttarakhand","tags":["culture","heritage"],"budget":6000,"sustainability":0.65,"crowd":0.75,"description":"One of Char Dham, Shiva temple at 3,583m, trekking through stunning mountain terrain"},

    # WEST BENGAL
    {"id":176,"name":"Darjeeling","state":"West Bengal","tags":["nature","culture"],"budget":5500,"sustainability":0.8,"crowd":0.55,"description":"Tea gardens, Tiger Hill sunrise with Kanchenjunga, toy train UNESCO heritage"},
    {"id":177,"name":"Sundarbans","state":"West Bengal","tags":["nature"],"budget":5000,"sustainability":0.88,"crowd":0.25,"description":"Largest mangrove forest in world, Royal Bengal Tigers that swim and UNESCO site"},
    {"id":178,"name":"Kolkata","state":"West Bengal","tags":["culture","heritage"],"budget":4000,"sustainability":0.5,"crowd":0.85,"description":"City of Joy with Victoria Memorial, Howrah Bridge, Durga Puja and rosogolla"},
    {"id":179,"name":"Kalimpong","state":"West Bengal","tags":["nature","culture"],"budget":4500,"sustainability":0.83,"crowd":0.3,"description":"Flower capital of India, Morgan House, Deolo Hill and Zong Dog Palri monastery"},
]

# ─── DQN Agent ───────────────────────────────────────────────────────────────

GAMMA = 0.95
EPSILON = 0.3
LEARNING_RATE = 0.1
ACTION_SIZE = len(DESTINATIONS)

q_table = np.zeros((1000, ACTION_SIZE))
replay_buffer = deque(maxlen=500)
interaction_count = 0

def state_to_index(state: list) -> int:
    discretized = [int(s * 10) for s in state]
    return abs(hash(tuple(discretized))) % 1000

def get_state(prefs: dict) -> list:
    budget_mid = (prefs["budget_min"] + prefs["budget_max"]) / 2
    budget_norm = min(budget_mid / 100000.0, 1.0)
    return [
        budget_norm,
        1.0 if prefs["travel_type"] == "nature"   else 0.0,
        1.0 if prefs["travel_type"] == "heritage" else 0.0,
        1.0 if prefs["travel_type"] == "beach"    else 0.0,
        1.0 if prefs["travel_type"] == "culture"  else 0.0,
        prefs["sustainability_pref"] / 10.0,
    ]

def score_destination(dest: dict, prefs: dict) -> float:
    budget_min = prefs["budget_min"]
    budget_max = prefs["budget_max"]
    dest_cost  = dest["budget"]

    if budget_min <= dest_cost <= budget_max:
        budget_fit = 1.0
    else:
        distance = max(dest_cost - budget_max, budget_min - dest_cost, 0)
        budget_fit = max(0.0, 1.0 - distance / max(budget_max, 1))

    tags = dest["tags"]
    if prefs["travel_type"] == tags[0]:
        type_match = 1.0
    elif prefs["travel_type"] in tags:
        type_match = 0.75
    else:
        type_match = 0.0

    sust_score = dest["sustainability"] * (prefs["sustainability_pref"] / 10.0)
    crowd_pen  = 1.0 - dest["crowd"] * 0.4

    return (budget_fit * 0.35) + (type_match * 0.40) + (sust_score * 0.15) + (crowd_pen * 0.10)

def update_q_table(state_idx: int, action: int, reward: float, next_state_idx: int):
    current_q  = q_table[state_idx][action]
    max_next_q = np.max(q_table[next_state_idx])
    new_q = current_q + LEARNING_RATE * (reward + GAMMA * max_next_q - current_q)
    q_table[state_idx][action] = new_q

class UserPreferences(BaseModel):
    budget_min: int
    budget_max: int
    travel_type: str
    sustainability_pref: int
    user_id: str

class FeedbackRequest(BaseModel):
    user_id: str
    destination_id: int
    liked: bool
    budget_min: int
    budget_max: int
    travel_type: str
    sustainability_pref: int

@app.get("/")
def root():
    return {"status": "Smart Tourism RL API is running", "total_destinations": len(DESTINATIONS)}

@app.post("/recommend")
def recommend(prefs: UserPreferences):
    global interaction_count, EPSILON

    state     = get_state(prefs.dict())
    state_idx = state_to_index(state)

    scored = []
    for dest in DESTINATIONS:
        score   = score_destination(dest, prefs.dict())
        q_val   = float(q_table[state_idx][dest["id"]])
        blended = score * 0.5 + (q_val / (abs(q_val) + 1)) * 0.5
        in_budget = prefs.budget_min <= dest["budget"] <= prefs.budget_max

        scored.append({
            "id":             dest["id"],
            "name":           dest["name"],
            "state":          dest["state"],
            "type":           dest["tags"][0],
            "tags":           dest["tags"],
            "description":    dest["description"],
            "estimated_cost": dest["budget"],
            "sustainability": round(dest["sustainability"] * 10, 1),
            "crowd_level":    "Low" if dest["crowd"] < 0.4 else ("Medium" if dest["crowd"] < 0.7 else "High"),
            "score":          round(blended, 3),
            "match_reason":   _match_reason(dest, prefs.dict(), in_budget),
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    interaction_count += 1
    EPSILON = max(0.05, EPSILON * 0.99)

    # Diversity filter — max 2 per state
    seen_states = {}
    diverse = []
    for item in scored:
        state = item["state"]
        if seen_states.get(state, 0) < 1:
            diverse.append(item)
            seen_states[state] = seen_states.get(state, 0) + 1
        if len(diverse) == 10:
            break

    return {
        "recommendations": diverse,
        "model_info": {
            "interactions": interaction_count,
            "exploration_rate": round(EPSILON, 3),
            "learning_mode": "exploring" if EPSILON > 0.15 else "exploiting",
        }
    }

@app.post("/feedback")
def feedback(fb: FeedbackRequest):
    prefs = {
        "budget_min": fb.budget_min,
        "budget_max": fb.budget_max,
        "travel_type": fb.travel_type,
        "sustainability_pref": fb.sustainability_pref,
    }
    state     = get_state(prefs)
    state_idx = state_to_index(state)
    reward    = 1.0 if fb.liked else -0.5

    replay_buffer.append((state_idx, fb.destination_id, reward, state_idx))
    batch = random.sample(replay_buffer, min(16, len(replay_buffer)))
    for s, a, r, ns in batch:
        update_q_table(s, a, r, ns)

    return {"status": "Model updated", "reward_applied": reward}

@app.get("/destinations")
def get_destinations():
    return {"destinations": DESTINATIONS, "total": len(DESTINATIONS)}

def _match_reason(dest: dict, prefs: dict, in_budget: bool) -> str:
    reasons = []
    if in_budget:
        reasons.append("fits your budget range")
    if prefs["travel_type"] in dest["tags"]:
        reasons.append(f"matches your {prefs['travel_type']} preference")
    if dest["sustainability"] >= 0.8:
        reasons.append("highly sustainable")
    if dest["crowd"] < 0.4:
        reasons.append("low crowds")
    return ", ".join(reasons) if reasons else "recommended based on past trips"