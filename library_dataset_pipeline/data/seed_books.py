"""
SEED_BOOKS
==========
A curated set of REAL, well-known, published books used as a demonstration
sample for the pipeline (84 real, unique books after dedup, spanning ~19 genres).

IMPORTANT ACCURACY NOTE:
- Title, author, original publisher, first-publication year, genre, and the
  factual description content are drawn from well-established public
  knowledge of these (very famous) books.
- ISBN-13 values are best-effort common-edition identifiers. ISBNs vary by
  edition/printing, so before importing into production, re-resolve every
  ISBN against the Open Library / Google Books APIs using pipeline/download.py
  (this file's do NOT skip that step in real usage).
- avg_rating / rating_count are illustrative approximations (order-of-
  magnitude realistic for these titles), not scraped live figures. Replace
  with live Google Books / Goodreads figures via download.py before
  production use.
- cover_url / thumbnail_url use Open Library's public covers API URL pattern
  (https://covers.openlibrary.org/b/isbn/{isbn13}-L.jpg), which resolves
  correctly whenever Open Library has that ISBN in its catalog.
"""

SEED_BOOKS = [
    # ---------------- LITERARY FICTION ----------------
    dict(title="To Kill a Mockingbird", subtitle=None, authors=["Harper Lee"],
         isbn13="9780061120084", isbn10="0061120081", publisher="J.B. Lippincott & Co.",
         pub_year=1960, language="en", pages=336, genre="Literary Fiction", subgenre="Coming-of-Age",
         description="A young girl in a small Alabama town watches her father, a principled lawyer, "
                      "defend a Black man falsely accused of a crime, and comes to understand "
                      "prejudice, courage, and moral growth in her community.",
         subjects=["racism", "justice", "childhood", "American South", "morality"],
         historical_period="1930s", country_setting="USA", time_setting="1930s",
         avg_rating=4.3, rating_count=5200000),

    dict(title="The Great Gatsby", subtitle=None, authors=["F. Scott Fitzgerald"],
         isbn13="9780743273565", isbn10="0743273567", publisher="Charles Scribner's Sons",
         pub_year=1925, language="en", pages=180, genre="Literary Fiction", subgenre="Tragedy",
         description="A mysterious millionaire's obsessive pursuit of a lost love unfolds against "
                      "the excess of the Jazz Age, exposing the hollowness beneath the American Dream.",
         subjects=["wealth", "love", "American Dream", "class", "1920s"],
         historical_period="1920s", country_setting="USA", time_setting="1920s",
         avg_rating=3.9, rating_count=4700000),

    dict(title="Beloved", subtitle=None, authors=["Toni Morrison"],
         isbn13="9781400033416", isbn10="1400033411", publisher="Alfred A. Knopf",
         pub_year=1987, language="en", pages=324, genre="Literary Fiction", subgenre="Historical",
         description="A formerly enslaved woman is haunted, literally and figuratively, by the "
                      "trauma of her past when a mysterious young woman arrives at her home.",
         subjects=["slavery", "trauma", "motherhood", "memory", "haunting"],
         historical_period="Post-Civil War", country_setting="USA", time_setting="1870s",
         avg_rating=3.9, rating_count=350000),

    dict(title="The Kite Runner", subtitle=None, authors=["Khaled Hosseini"],
         isbn13="9781594631931", isbn10="1594631931", publisher="Riverhead Books",
         pub_year=2003, language="en", pages=371, genre="Literary Fiction", subgenre="Historical",
         description="A boy's betrayal of his closest friend in Kabul haunts him into adulthood, "
                      "driving a journey of guilt, war, and an attempt at redemption decades later.",
         subjects=["friendship", "guilt", "Afghanistan", "war", "redemption"],
         historical_period="Late 20th century", country_setting="Afghanistan", time_setting="1970s-2000s",
         avg_rating=4.3, rating_count=2900000),

    # ---------------- SCIENCE FICTION ----------------
    dict(title="Dune", subtitle=None, authors=["Frank Herbert"],
         isbn13="9780441172719", isbn10="0441172717", publisher="Chilton Books",
         pub_year=1965, language="en", pages=412, genre="Science Fiction", subgenre="Space Opera",
         description="On a desert planet that is the sole source of a universe-altering substance, "
                      "a young heir becomes entangled in prophecy, ecology, and interstellar politics.",
         subjects=["politics", "ecology", "prophecy", "empire", "desert survival"],
         historical_period="Future", country_setting="Fictional/Arrakis", time_setting="Distant Future",
         avg_rating=4.25, rating_count=1200000),

    dict(title="Project Hail Mary", subtitle=None, authors=["Andy Weir"],
         isbn13="9780593135204", isbn10="0593135202", publisher="Ballantine Books",
         pub_year=2021, language="en", pages=496, genre="Science Fiction", subgenre="Hard Sci-Fi",
         description="A lone astronaut wakes with no memory on a solo mission to save Earth from "
                      "an extinction-level threat, and must solve science-driven puzzles to survive.",
         subjects=["space travel", "survival", "first contact", "science", "memory loss"],
         historical_period="Near Future", country_setting="Space/Earth", time_setting="Near Future",
         avg_rating=4.5, rating_count=750000),

    dict(title="Neuromancer", subtitle=None, authors=["William Gibson"],
         isbn13="9780441569595", isbn10="0441569595", publisher="Ace Books",
         pub_year=1984, language="en", pages=271, genre="Science Fiction", subgenre="Cyberpunk",
         description="A washed-up computer hacker is hired for one last job that pulls him into a "
                      "dangerous conspiracy involving artificial intelligence and corporate power.",
         subjects=["hacking", "artificial intelligence", "cyberpunk", "corporations", "virtual reality"],
         historical_period="Future", country_setting="Global/Cyberspace", time_setting="Near Future",
         avg_rating=3.9, rating_count=210000),

    dict(title="Ender's Game", subtitle=None, authors=["Orson Scott Card"],
         isbn13="9780812550702", isbn10="0812550706", publisher="Tor Books",
         pub_year=1985, language="en", pages=324, genre="Science Fiction", subgenre="Military Sci-Fi",
         description="A gifted child is trained in a brutal military academy to command Earth's "
                      "fleet against an alien threat, at steep personal and moral cost.",
         subjects=["war", "childhood", "leadership", "strategy", "alien invasion"],
         historical_period="Future", country_setting="Earth/Space", time_setting="Future",
         avg_rating=4.3, rating_count=1500000),

    # ---------------- FANTASY ----------------
    dict(title="The Hobbit", subtitle=None, authors=["J.R.R. Tolkien"],
         isbn13="9780547928227", isbn10="0547928223", publisher="George Allen & Unwin",
         pub_year=1937, language="en", pages=310, genre="Fantasy", subgenre="High Fantasy",
         description="A reluctant, home-loving hobbit is swept into a quest with a band of dwarves "
                      "to reclaim treasure guarded by a dragon, discovering unexpected courage along the way.",
         subjects=["quest", "dragons", "friendship", "courage", "mythology"],
         historical_period="Mythic Past", country_setting="Middle-earth", time_setting="Fantasy World",
         avg_rating=4.28, rating_count=3400000),

    dict(title="A Game of Thrones", subtitle=None, authors=["George R.R. Martin"],
         isbn13="9780553573404", isbn10="0553573403", publisher="Bantam Spectra",
         pub_year=1996, language="en", pages=694, genre="Fantasy", subgenre="Epic Fantasy",
         description="Noble houses vie for control of a fractured kingdom while an ancient threat "
                      "stirs beyond a great northern wall, in a story of politics, betrayal, and war.",
         subjects=["politics", "war", "betrayal", "power", "dragons"],
         historical_period="Medieval-inspired", country_setting="Westeros (Fictional)", time_setting="Fantasy World",
         avg_rating=4.44, rating_count=2400000),

    dict(title="The Name of the Wind", subtitle=None, authors=["Patrick Rothfuss"],
         isbn13="9780756404741", isbn10="0756404746", publisher="DAW Books",
         pub_year=2007, language="en", pages=662, genre="Fantasy", subgenre="Epic Fantasy",
         description="A legendary figure recounts his own life story, from a childhood in a traveling "
                      "troupe to his years of poverty and study at a university of magic.",
         subjects=["magic", "music", "coming of age", "university", "legend"],
         historical_period="Medieval-inspired", country_setting="Fictional World", time_setting="Fantasy World",
         avg_rating=4.53, rating_count=900000),

    dict(title="Circe", subtitle=None, authors=["Madeline Miller"],
         isbn13="9780316556347", isbn10="0316556349", publisher="Little, Brown and Company",
         pub_year=2018, language="en", pages=393, genre="Fantasy", subgenre="Mythological Fiction",
         description="A minor goddess exiled for her unruly power comes into her own on a lonely "
                      "island, crossing paths with figures from Greek myth and forging her own fate.",
         subjects=["mythology", "gods", "transformation", "independence", "witchcraft"],
         historical_period="Ancient", country_setting="Greece (Mythical)", time_setting="Ancient",
         avg_rating=4.28, rating_count=650000),

    # ---------------- MYSTERY / THRILLER ----------------
    dict(title="Gone Girl", subtitle=None, authors=["Gillian Flynn"],
         isbn13="9780307588371", isbn10="0307588378", publisher="Crown Publishing",
         pub_year=2012, language="en", pages=419, genre="Mystery/Thriller", subgenre="Psychological Thriller",
         description="When a woman vanishes on her wedding anniversary, suspicion falls on her "
                      "husband, and the unraveling truth reveals a marriage built on deception.",
         subjects=["marriage", "deception", "media", "psychology", "crime"],
         historical_period="Contemporary", country_setting="USA", time_setting="Present Day",
         avg_rating=4.11, rating_count=2600000),

    dict(title="The Silent Patient", subtitle=None, authors=["Alex Michaelides"],
         isbn13="9781250301697", isbn10="1250301696", publisher="Celadon Books",
         pub_year=2019, language="en", pages=336, genre="Mystery/Thriller", subgenre="Psychological Thriller",
         description="A woman stops speaking after allegedly murdering her husband, and the "
                      "psychotherapist determined to treat her uncovers a shocking hidden motive.",
         subjects=["psychology", "murder", "therapy", "silence", "obsession"],
         historical_period="Contemporary", country_setting="UK", time_setting="Present Day",
         avg_rating=4.15, rating_count=1300000),

    dict(title="The Da Vinci Code", subtitle=None, authors=["Dan Brown"],
         isbn13="9780307474278", isbn10="0307474275", publisher="Doubleday",
         pub_year=2003, language="en", pages=489, genre="Mystery/Thriller", subgenre="Conspiracy Thriller",
         description="A symbologist races across Europe to decode clues hidden in famous artworks, "
                      "unraveling a centuries-old secret tied to a powerful religious mystery.",
         subjects=["conspiracy", "religion", "art", "codes", "history"],
         historical_period="Contemporary", country_setting="France/UK", time_setting="Present Day",
         avg_rating=3.87, rating_count=2100000),

    dict(title="In the Woods", subtitle=None, authors=["Tana French"],
         isbn13="9780143113492", isbn10="014311349X", publisher="Viking Press",
         pub_year=2007, language="en", pages=429, genre="Mystery/Thriller", subgenre="Detective Fiction",
         description="A detective investigating a child's murder in his hometown must confront the "
                      "unsolved disappearance of his own childhood friends decades earlier.",
         subjects=["murder investigation", "memory", "childhood trauma", "small town", "detective"],
         historical_period="Contemporary", country_setting="Ireland", time_setting="Present Day",
         avg_rating=3.86, rating_count=280000),

    # ---------------- ROMANCE ----------------
    dict(title="Outlander", subtitle=None, authors=["Diana Gabaldon"],
         isbn13="9780440212560", isbn10="0440212561", publisher="Delacorte Press",
         pub_year=1991, language="en", pages=627, genre="Romance", subgenre="Time-Travel Romance",
         description="A World War II nurse is mysteriously transported to 18th-century Scotland, "
                      "where she is torn between two centuries and two very different loves.",
         subjects=["time travel", "Scotland", "war", "love triangle", "history"],
         historical_period="1740s", country_setting="Scotland", time_setting="1940s/1740s",
         avg_rating=4.25, rating_count=900000),

    dict(title="Me Before You", subtitle=None, authors=["Jojo Moyes"],
         isbn13="9780143124542", isbn10="0143124544", publisher="Penguin Books",
         pub_year=2012, language="en", pages=369, genre="Romance", subgenre="Contemporary Romance",
         description="A young woman hired to care for a paralyzed former businessman forms an "
                      "unexpected bond with him that challenges both their views on how to live.",
         subjects=["disability", "caregiving", "love", "choice", "grief"],
         historical_period="Contemporary", country_setting="UK", time_setting="Present Day",
         avg_rating=4.24, rating_count=1600000),

    dict(title="The Hating Game", subtitle=None, authors=["Sally Thorne"],
         isbn13="9780062439598", isbn10="0062439594", publisher="William Morrow",
         pub_year=2016, language="en", pages=384, genre="Romance", subgenre="Romantic Comedy",
         description="Two rival co-workers locked in a relentless office feud discover their "
                      "antagonism is masking a very different kind of tension.",
         subjects=["enemies to lovers", "workplace", "banter", "rivalry", "humor"],
         historical_period="Contemporary", country_setting="USA", time_setting="Present Day",
         avg_rating=4.13, rating_count=500000),

    dict(title="It Ends with Us", subtitle=None, authors=["Colleen Hoover"],
         isbn13="9781501110368", isbn10="1501110365", publisher="Atria Books",
         pub_year=2016, language="en", pages=384, genre="Romance", subgenre="Contemporary Romance",
         description="A young woman's whirlwind romance forces her to confront patterns of abuse "
                      "she witnessed in her own childhood and to make a difficult choice about her future.",
         subjects=["domestic abuse", "resilience", "love", "family patterns", "courage"],
         historical_period="Contemporary", country_setting="USA", time_setting="Present Day",
         avg_rating=4.25, rating_count=2500000),

    # ---------------- NONFICTION / SCIENCE ----------------
    dict(title="Sapiens: A Brief History of Humankind", subtitle=None, authors=["Yuval Noah Harari"],
         isbn13="9780062316097", isbn10="0062316095", publisher="Harper",
         pub_year=2014, language="en", pages=443, genre="Nonfiction", subgenre="Popular Science/History",
         description="A sweeping account of how Homo sapiens came to dominate the planet, tracing "
                      "the cognitive, agricultural, and scientific revolutions that shaped civilization.",
         subjects=["human evolution", "history", "anthropology", "civilization", "society"],
         historical_period="All of human history", country_setting="Global", time_setting="Non-fiction/Timeless",
         avg_rating=4.37, rating_count=1400000),

    dict(title="A Brief History of Time", subtitle=None, authors=["Stephen Hawking"],
         isbn13="9780553380163", isbn10="0553380168", publisher="Bantam Books",
         pub_year=1988, language="en", pages=256, genre="Nonfiction", subgenre="Popular Science",
         description="A physicist explains the origins of the universe, black holes, and the nature "
                      "of time and space in terms accessible to general readers.",
         subjects=["cosmology", "physics", "black holes", "time", "universe"],
         historical_period="Non-fiction", country_setting="Global", time_setting="Non-fiction/Timeless",
         avg_rating=4.18, rating_count=750000),

    dict(title="Thinking, Fast and Slow", subtitle=None, authors=["Daniel Kahneman"],
         isbn13="9780374533557", isbn10="0374533555", publisher="Farrar, Straus and Giroux",
         pub_year=2011, language="en", pages=499, genre="Nonfiction", subgenre="Psychology",
         description="A Nobel laureate psychologist explains the two systems that drive human "
                      "thought, revealing the biases and shortcuts behind everyday decisions.",
         subjects=["psychology", "decision making", "cognitive bias", "economics", "behavior"],
         historical_period="Non-fiction", country_setting="Global", time_setting="Non-fiction/Timeless",
         avg_rating=4.19, rating_count=550000),

    dict(title="Atomic Habits", subtitle="An Easy & Proven Way to Build Good Habits & Break Bad Ones",
         authors=["James Clear"], isbn13="9780735211292", isbn10="0735211299", publisher="Avery",
         pub_year=2018, language="en", pages=320, genre="Nonfiction", subgenre="Self-Help/Productivity",
         description="A practical guide to building better habits through small, consistent changes, "
                      "grounded in behavioral science and real-world examples.",
         subjects=["habits", "productivity", "self-improvement", "behavior change", "goals"],
         historical_period="Non-fiction", country_setting="Global", time_setting="Non-fiction/Timeless",
         avg_rating=4.37, rating_count=800000),

    # ---------------- HISTORY / BIOGRAPHY ----------------
    dict(title="The Diary of a Young Girl", subtitle=None, authors=["Anne Frank"],
         isbn13="9780553296983", isbn10="0553296981", publisher="Contact Publishing",
         pub_year=1947, language="en", pages=283, genre="Biography", subgenre="Memoir/History",
         description="The personal diary of a Jewish teenager hiding with her family in Amsterdam "
                      "during the Nazi occupation, offering a firsthand account of hope amid horror.",
         subjects=["World War II", "Holocaust", "hiding", "family", "hope"],
         historical_period="1940s", country_setting="Netherlands", time_setting="1940s",
         avg_rating=4.16, rating_count=3200000),

    dict(title="Guns, Germs, and Steel", subtitle="The Fates of Human Societies", authors=["Jared Diamond"],
         isbn13="9780393317558", isbn10="0393317552", publisher="W. W. Norton & Company",
         pub_year=1997, language="en", pages=480, genre="Nonfiction", subgenre="History/Anthropology",
         description="An exploration of why some societies developed technology and empire faster "
                      "than others, argued through geography, agriculture, and disease rather than race.",
         subjects=["history", "geography", "civilization", "agriculture", "colonization"],
         historical_period="All of human history", country_setting="Global", time_setting="Non-fiction/Timeless",
         avg_rating=4.03, rating_count=350000),

    dict(title="Steve Jobs", subtitle=None, authors=["Walter Isaacson"],
         isbn13="9781451648539", isbn10="1451648537", publisher="Simon & Schuster",
         pub_year=2011, language="en", pages=656, genre="Biography", subgenre="Business Biography",
         description="An authorized biography of Apple's co-founder, drawing on extensive interviews "
                      "to portray his creative vision, perfectionism, and complicated personal life.",
         subjects=["technology", "innovation", "leadership", "Apple", "entrepreneurship"],
         historical_period="Late 20th-early 21st century", country_setting="USA", time_setting="1970s-2010s",
         avg_rating=4.18, rating_count=500000),

    dict(title="Unbroken", subtitle="A World War II Story of Survival, Resilience, and Redemption",
         authors=["Laura Hillenbrand"], isbn13="9781400064168", isbn10="1400064163",
         publisher="Random House", pub_year=2010, language="en", pages=473,
         genre="Biography", subgenre="War History",
         description="An Olympic runner turned WWII airman survives a plane crash, weeks adrift at "
                      "sea, and years in brutal prisoner-of-war camps in a story of endurance.",
         subjects=["World War II", "survival", "resilience", "prisoner of war", "sports"],
         historical_period="1940s", country_setting="Pacific Theater", time_setting="1940s",
         avg_rating=4.45, rating_count=750000),

    # ---------------- SELF-HELP / BUSINESS ----------------
    dict(title="How to Win Friends and Influence People", subtitle=None, authors=["Dale Carnegie"],
         isbn13="9780671027032", isbn10="0671027034", publisher="Simon & Schuster",
         pub_year=1936, language="en", pages=291, genre="Self-Help", subgenre="Communication",
         description="A foundational guide to building rapport, handling people diplomatically, and "
                      "communicating persuasively in personal and professional relationships.",
         subjects=["communication", "persuasion", "relationships", "leadership", "influence"],
         historical_period="Non-fiction", country_setting="Global", time_setting="Non-fiction/Timeless",
         avg_rating=4.2, rating_count=750000),

    dict(title="Rich Dad Poor Dad", subtitle=None, authors=["Robert Kiyosaki"],
         isbn13="9781612680194", isbn10="1612680194", publisher="Plata Publishing",
         pub_year=1997, language="en", pages=336, genre="Business", subgenre="Personal Finance",
         description="Contrasting lessons from two father figures illustrate different attitudes "
                      "toward money, assets, and financial independence.",
         subjects=["personal finance", "investing", "financial literacy", "assets", "money mindset"],
         historical_period="Non-fiction", country_setting="Global", time_setting="Non-fiction/Timeless",
         avg_rating=4.09, rating_count=600000),

    dict(title="The Lean Startup", subtitle=None, authors=["Eric Ries"],
         isbn13="9780307887894", isbn10="0307887898", publisher="Crown Business",
         pub_year=2011, language="en", pages=336, genre="Business", subgenre="Entrepreneurship",
         description="A methodology for building startups through rapid experimentation, validated "
                      "learning, and iterative product development rather than big upfront planning.",
         subjects=["entrepreneurship", "startups", "product development", "innovation", "management"],
         historical_period="Non-fiction", country_setting="Global", time_setting="Non-fiction/Timeless",
         avg_rating=4.08, rating_count=210000),

    dict(title="Grit", subtitle="The Power of Passion and Perseverance", authors=["Angela Duckworth"],
         isbn13="9781501111112", isbn10="1501111108", publisher="Scribner",
         pub_year=2016, language="en", pages=352, genre="Self-Help", subgenre="Psychology",
         description="A psychologist argues that sustained passion and perseverance, more than "
                      "talent, predict long-term achievement, drawing on research and case studies.",
         subjects=["perseverance", "achievement", "psychology", "motivation", "success"],
         historical_period="Non-fiction", country_setting="Global", time_setting="Non-fiction/Timeless",
         avg_rating=4.1, rating_count=200000),

    # ---------------- YOUNG ADULT ----------------
    dict(title="The Fault in Our Stars", subtitle=None, authors=["John Green"],
         isbn13="9780525478812", isbn10="0525478817", publisher="Dutton Books",
         pub_year=2012, language="en", pages=313, genre="Young Adult", subgenre="Contemporary Romance",
         description="Two teenagers who meet at a cancer support group fall in love while grappling "
                      "with mortality, meaning, and what it means to leave a mark on the world.",
         subjects=["illness", "love", "mortality", "friendship", "coming of age"],
         historical_period="Contemporary", country_setting="USA", time_setting="Present Day",
         avg_rating=4.13, rating_count=4700000),

    dict(title="The Hunger Games", subtitle=None, authors=["Suzanne Collins"],
         isbn13="9780439023528", isbn10="0439023521", publisher="Scholastic Press",
         pub_year=2008, language="en", pages=374, genre="Young Adult", subgenre="Dystopian",
         description="In a totalitarian nation, a teenage girl volunteers to take her sister's place "
                      "in a televised fight to the death, sparking rebellion against the ruling elite.",
         subjects=["dystopia", "survival", "rebellion", "inequality", "media"],
         historical_period="Future", country_setting="Fictional/Panem", time_setting="Post-Apocalyptic",
         avg_rating=4.33, rating_count=8000000),

    dict(title="Harry Potter and the Sorcerer's Stone", subtitle=None, authors=["J.K. Rowling"],
         isbn13="9780590353427", isbn10="0590353403", publisher="Scholastic",
         pub_year=1997, language="en", pages=309, genre="Young Adult", subgenre="Fantasy",
         description="An orphaned boy discovers he is a wizard on his eleventh birthday and enrolls "
                      "in a magical school, where he begins uncovering the truth about his past.",
         subjects=["magic", "friendship", "school", "good vs evil", "identity"],
         historical_period="Contemporary", country_setting="UK", time_setting="1990s",
         avg_rating=4.47, rating_count=9500000),

    dict(title="Percy Jackson and the Lightning Thief", subtitle=None, authors=["Rick Riordan"],
         isbn13="9780786838653", isbn10="0786838655", publisher="Disney-Hyperion",
         pub_year=2005, language="en", pages=377, genre="Young Adult", subgenre="Mythological Fantasy",
         description="A boy discovers he is the son of a Greek god and is drawn into a quest across "
                      "modern America to prevent a war among the gods of Olympus.",
         subjects=["mythology", "gods", "quest", "identity", "friendship"],
         historical_period="Contemporary", country_setting="USA", time_setting="Present Day",
         avg_rating=4.28, rating_count=2200000),

    # ---------------- CHILDREN'S ----------------
    dict(title="Charlotte's Web", subtitle=None, authors=["E.B. White"],
         isbn13="9780061124952", isbn10="0061124951", publisher="Harper & Brothers",
         pub_year=1952, language="en", pages=184, genre="Children's", subgenre="Animal Fiction",
         description="A spider befriends a young pig destined for slaughter and uses clever wordplay "
                      "in her web to save his life, a story of friendship and sacrifice.",
         subjects=["friendship", "farm life", "sacrifice", "animals", "loyalty"],
         historical_period="Mid-20th century", country_setting="USA", time_setting="1950s",
         avg_rating=4.19, rating_count=1300000),

    dict(title="Where the Wild Things Are", subtitle=None, authors=["Maurice Sendak"],
         isbn13="9780064431781", isbn10="0064431783", publisher="Harper & Row",
         pub_year=1963, language="en", pages=48, genre="Children's", subgenre="Picture Book",
         description="A misbehaving boy sails to an island of monstrous creatures who crown him "
                      "their king, before he chooses to return home to where he is loved.",
         subjects=["imagination", "emotions", "family", "adventure", "monsters"],
         historical_period="Mid-20th century", country_setting="Fictional/USA", time_setting="Timeless",
         avg_rating=4.24, rating_count=350000),

    dict(title="Matilda", subtitle=None, authors=["Roald Dahl"],
         isbn13="9780142410370", isbn10="0142410373", publisher="Jonathan Cape",
         pub_year=1988, language="en", pages=240, genre="Children's", subgenre="Fantasy",
         description="A brilliant, neglected girl with a gift for telepathy uses her wits and hidden "
                      "powers to stand up to her cruel family and a tyrannical headmistress.",
         subjects=["intelligence", "justice", "school", "family", "empowerment"],
         historical_period="Contemporary", country_setting="UK", time_setting="1980s",
         avg_rating=4.29, rating_count=1300000),

    dict(title="The Very Hungry Caterpillar", subtitle=None, authors=["Eric Carle"],
         isbn13="9780399226908", isbn10="0399226907", publisher="World Publishing Company",
         pub_year=1969, language="en", pages=26, genre="Children's", subgenre="Picture Book",
         description="A tiny caterpillar eats its way through a week of different foods before "
                      "transforming into a butterfly, in a simple story about growth and change.",
         subjects=["growth", "transformation", "counting", "food", "nature"],
         historical_period="Timeless", country_setting="Global", time_setting="Timeless",
         avg_rating=4.34, rating_count=550000),

    # ---------------- HORROR ----------------
    dict(title="It", subtitle=None, authors=["Stephen King"],
         isbn13="9781501142970", isbn10="1501142976", publisher="Viking Press",
         pub_year=1986, language="en", pages=1138, genre="Horror", subgenre="Supernatural Horror",
         description="A group of childhood friends reunite as adults to confront a shape-shifting "
                      "entity that preys on children in their hometown, decades after their first encounter.",
         subjects=["fear", "childhood trauma", "small town", "supernatural", "friendship"],
         historical_period="Mixed 1950s/1980s", country_setting="USA", time_setting="1950s-1980s",
         avg_rating=4.25, rating_count=1200000),

    dict(title="Dracula", subtitle=None, authors=["Bram Stoker"],
         isbn13="9780486411095", isbn10="0486411099", publisher="Archibald Constable and Company",
         pub_year=1897, language="en", pages=418, genre="Horror", subgenre="Gothic Horror",
         description="A Transylvanian count's plan to spread his curse to England is opposed by a "
                      "small group who must learn his supernatural weaknesses to stop him.",
         subjects=["vampires", "gothic", "good vs evil", "superstition", "Victorian era"],
         historical_period="Victorian", country_setting="England/Transylvania", time_setting="1890s",
         avg_rating=4.02, rating_count=900000),

    dict(title="The Shining", subtitle=None, authors=["Stephen King"],
         isbn13="9780307743657", isbn10="0307743659", publisher="Doubleday",
         pub_year=1977, language="en", pages=447, genre="Horror", subgenre="Psychological Horror",
         description="A writer takes a winter caretaking job at an isolated, haunted hotel, where "
                      "supernatural forces exploit his personal demons and endanger his family.",
         subjects=["isolation", "family", "addiction", "supernatural", "madness"],
         historical_period="Contemporary (1970s)", country_setting="USA", time_setting="1970s",
         avg_rating=4.26, rating_count=1000000),

    dict(title="Frankenstein", subtitle="Or, The Modern Prometheus", authors=["Mary Shelley"],
         isbn13="9780486282114", isbn10="0486282112", publisher="Lackington, Hughes, Harding, Mavor & Jones",
         pub_year=1818, language="en", pages=280, genre="Horror", subgenre="Gothic/Science Fiction",
         description="A scientist's creation of an artificial being ends in tragedy, raising early "
                      "questions about ambition, responsibility, and what makes someone monstrous.",
         subjects=["science", "ambition", "creation", "isolation", "morality"],
         historical_period="Romantic era", country_setting="Europe", time_setting="Late 1700s",
         avg_rating=3.87, rating_count=1200000),

    # ---------------- CLASSICS / POETRY ----------------
    dict(title="Pride and Prejudice", subtitle=None, authors=["Jane Austen"],
         isbn13="9780141439518", isbn10="0141439513", publisher="T. Egerton, Whitehall",
         pub_year=1813, language="en", pages=432, genre="Classics", subgenre="Romantic Fiction",
         description="A sharp-witted young woman navigates courtship, family expectations, and her "
                      "own pride and misjudgments as she comes to reconsider a proud suitor.",
         subjects=["marriage", "class", "pride", "wit", "manners"],
         historical_period="Regency era", country_setting="England", time_setting="Early 1800s",
         avg_rating=4.28, rating_count=3600000),

    dict(title="1984", subtitle=None, authors=["George Orwell"],
         isbn13="9780451524935", isbn10="0451524934", publisher="Secker & Warburg",
         pub_year=1949, language="en", pages=328, genre="Classics", subgenre="Dystopian",
         description="In a totalitarian superstate under constant surveillance, a low-level worker "
                      "begins to question the regime's control over truth, language, and thought.",
         subjects=["totalitarianism", "surveillance", "propaganda", "freedom", "truth"],
         historical_period="Future (from 1949)", country_setting="Fictional/Oceania", time_setting="Dystopian",
         avg_rating=4.19, rating_count=4200000),

    dict(title="War and Peace", subtitle=None, authors=["Leo Tolstoy"],
         isbn13="9781400079988", isbn10="1400079985", publisher="The Russian Messenger",
         pub_year=1869, language="en", pages=1225, genre="Classics", subgenre="Historical Fiction",
         description="Interweaving the lives of several Russian aristocratic families during the "
                      "Napoleonic Wars, the novel explores love, fate, and the meaning of history.",
         subjects=["war", "aristocracy", "fate", "family", "history"],
         historical_period="Napoleonic era", country_setting="Russia", time_setting="Early 1800s",
         avg_rating=4.13, rating_count=350000),

    dict(title="Leaves of Grass", subtitle=None, authors=["Walt Whitman"],
         isbn13=None, isbn10=None,  # pre-1970 original predates the ISBN system;
         # no single verified modern-reprint ISBN — resolve via live API before import
         publisher="Self-published",
         pub_year=1855, language="en", pages=95, genre="Classics", subgenre="Poetry",
         description="A landmark poetry collection celebrating individuality, democracy, nature, and "
                      "the human body in free verse that broke from formal poetic convention.",
         subjects=["individuality", "democracy", "nature", "free verse", "America"],
         historical_period="19th century", country_setting="USA", time_setting="1850s",
         avg_rating=4.06, rating_count=45000),

    # ---------------- POETRY / CLASSICS (more) ----------------
    dict(title="The Odyssey", subtitle=None, authors=["Homer"],
         isbn13="9780140268867", isbn10=None, publisher="Penguin Classics",
         pub_year=-800, language="en", pages=541, genre="Classics", subgenre="Epic Poetry",
         description="After the fall of Troy, a Greek king spends ten years journeying home, "
                      "facing monsters, gods, and temptation while his wife fends off suitors.",
         subjects=["heroism", "mythology", "homecoming", "fate", "cunning"],
         historical_period="Ancient Greece", country_setting="Greece", time_setting="Ancient",
         avg_rating=3.85, rating_count=900000),

    dict(title="Crime and Punishment", subtitle=None, authors=["Fyodor Dostoevsky"],
         isbn13="9780143107637", isbn10=None, publisher="Penguin Classics",
         pub_year=1866, language="en", pages=671, genre="Classics", subgenre="Psychological Fiction",
         description="A destitute former student murders a pawnbroker and grapples with guilt, "
                      "justification, and redemption in Tsarist-era St. Petersburg.",
         subjects=["guilt", "morality", "poverty", "redemption", "crime"],
         historical_period="19th century", country_setting="Russia", time_setting="1860s",
         avg_rating=4.26, rating_count=780000),

    dict(title="One Hundred Years of Solitude", subtitle=None, authors=["Gabriel García Márquez"],
         isbn13="9780060883287", isbn10=None, publisher="Harper Perennial",
         pub_year=1967, language="en", pages=417, genre="Classics", subgenre="Magical Realism",
         description="Seven generations of the Buendía family live out love, war, and prophecy in "
                      "the mythical town of Macondo, blending myth and history into one saga.",
         subjects=["family", "magical realism", "time", "solitude", "Latin America"],
         historical_period="19th-20th century", country_setting="Colombia", time_setting="Multi-generational",
         avg_rating=4.12, rating_count=800000),

    # ---------------- BIOGRAPHY / MEMOIR ----------------
    dict(title="Educated", subtitle="A Memoir", authors=["Tara Westover"],
         isbn13="9780399590504", isbn10=None, publisher="Random House",
         pub_year=2018, language="en", pages=334, genre="Biography", subgenre="Memoir",
         description="Raised by survivalist parents in rural Idaho with no formal schooling, the "
                      "author claws her way to a Cambridge PhD while reckoning with family and identity.",
         subjects=["education", "family", "identity", "survivalism", "self-transformation"],
         historical_period="Contemporary", country_setting="USA", time_setting="1990s-2010s",
         avg_rating=4.47, rating_count=1400000),

    dict(title="Born a Crime", subtitle="Stories from a South African Childhood", authors=["Trevor Noah"],
         isbn13="9780399588174", isbn10=None, publisher="Spiegel & Grau",
         pub_year=2016, language="en", pages=304, genre="Biography", subgenre="Memoir",
         description="Comedian Trevor Noah recounts growing up mixed-race under apartheid South "
                      "Africa, where his very existence was illegal, through humor and hardship.",
         subjects=["apartheid", "race", "identity", "family", "South Africa"],
         historical_period="1980s-1990s", country_setting="South Africa", time_setting="Apartheid era",
         avg_rating=4.5, rating_count=650000),

    dict(title="Long Walk to Freedom", subtitle=None, authors=["Nelson Mandela"],
         isbn13="9780316548182", isbn10=None, publisher="Little, Brown and Company",
         pub_year=1994, language="en", pages=656, genre="Biography", subgenre="Autobiography",
         description="Nelson Mandela recounts his journey from rural childhood to 27 years of "
                      "imprisonment to becoming South Africa's first democratically elected president.",
         subjects=["apartheid", "leadership", "freedom", "activism", "South Africa"],
         historical_period="20th century", country_setting="South Africa", time_setting="1918-1994",
         avg_rating=4.35, rating_count=185000),

    # ---------------- SCIENCE / POPULAR NONFICTION ----------------
    dict(title="Cosmos", subtitle=None, authors=["Carl Sagan"],
         isbn13="9780345539434", isbn10=None, publisher="Ballantine Books",
         pub_year=1980, language="en", pages=384, genre="Science", subgenre="Popular Science",
         description="A sweeping tour of the universe, from the origins of life on Earth to the "
                      "possibility of extraterrestrial civilizations, told with wonder and rigor.",
         subjects=["astronomy", "science", "universe", "evolution", "space exploration"],
         historical_period="Contemporary", country_setting=None, time_setting="Present Day",
         avg_rating=4.44, rating_count=95000),

    dict(title="The Selfish Gene", subtitle=None, authors=["Richard Dawkins"],
         isbn13="9780198788607", isbn10=None, publisher="Oxford University Press",
         pub_year=1976, language="en", pages=360, genre="Science", subgenre="Evolutionary Biology",
         description="A gene-centered view of evolution argues that genes, not individuals or "
                      "species, are the primary unit of natural selection driving behavior.",
         subjects=["evolution", "genetics", "biology", "natural selection", "behavior"],
         historical_period="Contemporary", country_setting=None, time_setting="Present Day",
         avg_rating=4.14, rating_count=75000),

    dict(title="Silent Spring", subtitle=None, authors=["Rachel Carson"],
         isbn13="9780618249060", isbn10=None, publisher="Houghton Mifflin",
         pub_year=1962, language="en", pages=378, genre="Science", subgenre="Environmental Science",
         description="A landmark exposé on the environmental damage caused by pesticides, credited "
                      "with launching the modern environmental movement.",
         subjects=["environment", "ecology", "pesticides", "conservation", "activism"],
         historical_period="1960s", country_setting="USA", time_setting="1960s",
         avg_rating=4.26, rating_count=60000),

    # ---------------- HISTORY ----------------
    dict(title="Guns, Germs, and Steel", subtitle="The Fates of Human Societies", authors=["Jared Diamond"],
         isbn13="9780393317558", isbn10=None, publisher="W. W. Norton & Company",
         pub_year=1997, language="en", pages=480, genre="History", subgenre="World History",
         description="An exploration of why some civilizations conquered others, tracing the roots "
                      "of global inequality to geography, agriculture, and disease resistance.",
         subjects=["history", "geography", "civilization", "anthropology", "inequality"],
         historical_period="Prehistoric-Modern", country_setting=None, time_setting="Broad historical span",
         avg_rating=4.03, rating_count=310000),

    dict(title="The Diary of a Young Girl", subtitle=None, authors=["Anne Frank"],
         isbn13="9780553296983", isbn10=None, publisher="Bantam",
         pub_year=1947, language="en", pages=283, genre="History", subgenre="Memoir",
         description="A teenage girl's diary chronicling two years in hiding from Nazi persecution "
                      "in occupied Amsterdam, offering an intimate account of hope amid horror.",
         subjects=["Holocaust", "World War II", "identity", "hope", "diary"],
         historical_period="World War II", country_setting="Netherlands", time_setting="1942-1944",
         avg_rating=4.18, rating_count=3200000),

    # ---------------- PHILOSOPHY / SELF-HELP (more) ----------------
    dict(title="Man's Search for Meaning", subtitle=None, authors=["Viktor E. Frankl"],
         isbn13="9780807014295", isbn10=None, publisher="Beacon Press",
         pub_year=1946, language="en", pages=165, genre="Nonfiction", subgenre="Philosophy",
         description="A psychiatrist and Holocaust survivor argues that finding meaning, even in "
                      "the worst suffering, is what allows people to endure and persevere.",
         subjects=["meaning", "resilience", "psychology", "Holocaust", "philosophy"],
         historical_period="Contemporary", country_setting="Austria", time_setting="1940s-onward",
         avg_rating=4.37, rating_count=680000),

    dict(title="The Subtle Art of Not Giving a F*ck", subtitle=None, authors=["Mark Manson"],
         isbn13="9780062457714", isbn10=None, publisher="HarperOne",
         pub_year=2016, language="en", pages=224, genre="Nonfiction", subgenre="Self-Help",
         description="A counterintuitive self-help book arguing that a good life comes from caring "
                      "about fewer, better things instead of chasing constant positivity.",
         subjects=["self-improvement", "values", "mindset", "resilience", "happiness"],
         historical_period="Contemporary", country_setting=None, time_setting="Present Day",
         avg_rating=3.92, rating_count=750000),

    dict(title="Deep Work", subtitle="Rules for Focused Success in a Distracted World", authors=["Cal Newport"],
         isbn13="9781455586691", isbn10=None, publisher="Grand Central Publishing",
         pub_year=2016, language="en", pages=304, genre="Nonfiction", subgenre="Productivity",
         description="An argument for the value of focused, undistracted work in a world of "
                      "constant interruption, with practical strategies for cultivating deep focus.",
         subjects=["productivity", "focus", "work", "attention", "career"],
         historical_period="Contemporary", country_setting=None, time_setting="Present Day",
         avg_rating=4.19, rating_count=115000),

    # ---------------- TECH / PROGRAMMING ----------------
    dict(title="Clean Code", subtitle="A Handbook of Agile Software Craftsmanship", authors=["Robert C. Martin"],
         isbn13="9780132350884", isbn10=None, publisher="Prentice Hall",
         pub_year=2008, language="en", pages=464, genre="Technology", subgenre="Software Engineering",
         description="A guide to writing readable, maintainable code through naming, functions, "
                      "and design principles, illustrated with refactoring case studies.",
         subjects=["programming", "software engineering", "best practices", "refactoring", "code quality"],
         historical_period="Contemporary", country_setting=None, time_setting="Present Day",
         avg_rating=4.19, rating_count=115000),

    dict(title="Introduction to Algorithms", subtitle=None,
         authors=["Thomas H. Cormen", "Charles E. Leiserson", "Ronald L. Rivest", "Clifford Stein"],
         isbn13="9780262046305", isbn10=None, publisher="MIT Press",
         pub_year=1990, language="en", pages=1312, genre="Technology", subgenre="Computer Science",
         description="A comprehensive, rigorous textbook covering algorithm design, analysis, and "
                      "data structures, widely used in university computer science courses.",
         subjects=["algorithms", "computer science", "data structures", "complexity", "mathematics"],
         historical_period="Contemporary", country_setting=None, time_setting="Present Day",
         avg_rating=4.35, rating_count=25000),

    dict(title="Designing Data-Intensive Applications", subtitle=None, authors=["Martin Kleppmann"],
         isbn13="9781449373320", isbn10=None, publisher="O'Reilly Media",
         pub_year=2017, language="en", pages=616, genre="Technology", subgenre="Software Engineering",
         description="A deep dive into the principles behind reliable, scalable, and maintainable "
                      "data systems, covering databases, streaming, and distributed systems.",
         subjects=["databases", "distributed systems", "software architecture", "data engineering", "scalability"],
         historical_period="Contemporary", country_setting=None, time_setting="Present Day",
         avg_rating=4.48, rating_count=25000),

    # ---------------- ROMANCE (more) ----------------
    dict(title="The Notebook", subtitle=None, authors=["Nicholas Sparks"],
         isbn13="9780446605236", isbn10=None, publisher="Warner Books",
         pub_year=1996, language="en", pages=214, genre="Romance", subgenre="Contemporary Romance",
         description="A poor young man and a wealthy young woman fall in love one summer, only to "
                      "be separated by class and circumstance, with a devoted reunion decades later.",
         subjects=["love", "class", "memory", "devotion", "separation"],
         historical_period="1940s-1990s", country_setting="USA", time_setting="Mid-to-late 20th century",
         avg_rating=4.13, rating_count=1200000),

    dict(title="Beach Read", subtitle=None, authors=["Emily Henry"],
         isbn13="9781984806734", isbn10=None, publisher="Berkley",
         pub_year=2020, language="en", pages=361, genre="Romance", subgenre="Contemporary Romance",
         description="Two rival writers with writer's block, one a cynic and one a romantic, swap "
                      "genres for the summer and end up rewriting their assumptions about love.",
         subjects=["writing", "grief", "romance", "rivalry", "self-discovery"],
         historical_period="Contemporary", country_setting="USA", time_setting="Present Day",
         avg_rating=4.02, rating_count=650000),

    # ---------------- THRILLER / MYSTERY (more) ----------------
    dict(title="The Girl with the Dragon Tattoo", subtitle=None, authors=["Stieg Larsson"],
         isbn13="9780307949486", isbn10=None, publisher="Vintage Crime",
         pub_year=2005, language="en", pages=644, genre="Mystery", subgenre="Crime Thriller",
         description="A disgraced journalist and a brilliant hacker investigate a decades-old "
                      "disappearance, uncovering a trail of corporate corruption and violence.",
         subjects=["murder", "corruption", "journalism", "hacking", "family secrets"],
         historical_period="Contemporary", country_setting="Sweden", time_setting="Present Day",
         avg_rating=4.19, rating_count=2400000),

    dict(title="The Silence of the Lambs", subtitle=None, authors=["Thomas Harris"],
         isbn13="9780312924584", isbn10=None, publisher="St. Martin's Press",
         pub_year=1988, language="en", pages=338, genre="Mystery", subgenre="Psychological Thriller",
         description="A young FBI trainee seeks the counsel of an imprisoned cannibalistic "
                      "psychiatrist to catch a serial killer skinning his female victims.",
         subjects=["serial killer", "psychology", "FBI", "crime", "manipulation"],
         historical_period="Contemporary", country_setting="USA", time_setting="1980s",
         avg_rating=4.19, rating_count=340000),

    # ---------------- FANTASY / SCI-FI (more) ----------------
    dict(title="Mistborn: The Final Empire", subtitle=None, authors=["Brandon Sanderson"],
         isbn13="9780765350381", isbn10=None, publisher="Tor Books",
         pub_year=2006, language="en", pages=541, genre="Fantasy", subgenre="Epic Fantasy",
         description="In a world where ash falls from the sky and an immortal emperor rules through "
                      "terror, a street urchin with rare magical powers joins a heist to topple him.",
         subjects=["magic", "rebellion", "empire", "heist", "prophecy"],
         historical_period="Fantasy World", country_setting="Fantasy World", time_setting="Fantasy Era",
         avg_rating=4.47, rating_count=700000),

    dict(title="The Left Hand of Darkness", subtitle=None, authors=["Ursula K. Le Guin"],
         isbn13="9780441478125", isbn10=None, publisher="Ace Books",
         pub_year=1969, language="en", pages=304, genre="Science Fiction", subgenre="Social Science Fiction",
         description="An envoy from an interstellar alliance navigates the politics of a wintry "
                      "planet whose inhabitants have no fixed gender, challenging his assumptions.",
         subjects=["gender", "diplomacy", "alien culture", "identity", "politics"],
         historical_period="Future", country_setting="Fictional Planet", time_setting="Future",
         avg_rating=4.06, rating_count=115000),

    dict(title="Foundation", subtitle=None, authors=["Isaac Asimov"],
         isbn13="9780553293357", isbn10=None, publisher="Bantam Spectra",
         pub_year=1951, language="en", pages=255, genre="Science Fiction", subgenre="Space Opera",
         description="A mathematician predicts the fall of a galactic empire and establishes a "
                      "foundation to preserve knowledge and shorten the coming dark age.",
         subjects=["empire", "prediction", "civilization", "science", "politics"],
         historical_period="Future", country_setting="Galactic Empire", time_setting="Far Future",
         avg_rating=4.19, rating_count=350000),

    # ---------------- HORROR (more) ----------------
    dict(title="The Haunting of Hill House", subtitle=None, authors=["Shirley Jackson"],
         isbn13="9780143039983", isbn10=None, publisher="Penguin Classics",
         pub_year=1959, language="en", pages=246, genre="Horror", subgenre="Gothic Horror",
         description="Four strangers investigating paranormal activity at a notoriously haunted "
                      "mansion find the house's influence preying on their sanity, one by one.",
         subjects=["haunted house", "psychological horror", "isolation", "sanity", "supernatural"],
         historical_period="Contemporary", country_setting="USA", time_setting="1950s",
         avg_rating=3.98, rating_count=140000),

    dict(title="Rosemary's Baby", subtitle=None, authors=["Ira Levin"],
         isbn13="9781472234353", isbn10=None, publisher="Corsair",
         pub_year=1967, language="en", pages=245, genre="Horror", subgenre="Psychological Horror",
         description="A young wife in Manhattan grows suspicious that her eccentric neighbors and "
                      "her own husband are part of a satanic plot involving her unborn child.",
         subjects=["pregnancy", "paranoia", "cults", "marriage", "the occult"],
         historical_period="Contemporary", country_setting="USA", time_setting="1960s",
         avg_rating=4.02, rating_count=135000),

    # ---------------- CHILDREN / MG (more) ----------------
    dict(title="The Giving Tree", subtitle=None, authors=["Shel Silverstein"],
         isbn13="9780060256654", isbn10=None, publisher="Harper & Row",
         pub_year=1964, language="en", pages=64, genre="Children", subgenre="Picture Book",
         description="A tree gives everything it has, again and again, to a boy across his "
                      "lifetime, in a spare parable about generosity and selflessness.",
         subjects=["generosity", "love", "sacrifice", "nature", "growing up"],
         historical_period="Contemporary", country_setting=None, time_setting="Timeless",
         avg_rating=4.37, rating_count=1000000),

    dict(title="Diary of a Wimpy Kid", subtitle=None, authors=["Jeff Kinney"],
         isbn13="9780810993136", isbn10=None, publisher="Amulet Books",
         pub_year=2007, language="en", pages=217, genre="Children", subgenre="Middle Grade",
         description="A middle-schooler's illustrated diary chronicles the awkward, funny mishaps "
                      "of surviving school, friendships, and family with wry self-deprecation.",
         subjects=["school", "friendship", "family", "humor", "growing up"],
         historical_period="Contemporary", country_setting="USA", time_setting="Present Day",
         avg_rating=3.99, rating_count=2200000),

    dict(title="The Chronicles of Narnia: The Lion, the Witch and the Wardrobe", subtitle=None,
         authors=["C.S. Lewis"],
         isbn13="9780064404990", isbn10=None, publisher="Geoffrey Bles",
         pub_year=1950, language="en", pages=206, genre="Children", subgenre="Fantasy",
         description="Four siblings step through a magical wardrobe into the snowbound land of "
                      "Narnia, where they must help a lion king overthrow an eternal winter.",
         subjects=["magic", "siblings", "good vs evil", "sacrifice", "adventure"],
         historical_period="World War II era", country_setting="Fantasy World", time_setting="1940s/Timeless",
         avg_rating=4.26, rating_count=600000),

    # ---------------- BUSINESS (more) ----------------
    dict(title="Zero to One", subtitle="Notes on Startups, or How to Build the Future", authors=["Peter Thiel"],
         isbn13="9780804139298", isbn10=None, publisher="Crown Business",
         pub_year=2014, language="en", pages=224, genre="Business", subgenre="Entrepreneurship",
         description="A contrarian guide to building breakthrough companies, arguing true progress "
                      "comes from creating something new rather than copying what already works.",
         subjects=["entrepreneurship", "innovation", "startups", "monopoly", "technology"],
         historical_period="Contemporary", country_setting=None, time_setting="Present Day",
         avg_rating=4.18, rating_count=210000),

    dict(title="Good to Great", subtitle="Why Some Companies Make the Leap... and Others Don't",
         authors=["Jim Collins"],
         isbn13="9780066620992", isbn10=None, publisher="HarperBusiness",
         pub_year=2001, language="en", pages=320, genre="Business", subgenre="Management",
         description="A research-driven study of companies that achieved sustained excellence, "
                      "identifying leadership and discipline traits that separate good from great.",
         subjects=["leadership", "management", "business strategy", "discipline", "growth"],
         historical_period="Contemporary", country_setting=None, time_setting="Present Day",
         avg_rating=4.14, rating_count=140000),

    dict(title="Thinking, Fast and Slow", subtitle=None, authors=["Daniel Kahneman"],
         isbn13="9780374533557", isbn10=None, publisher="Farrar, Straus and Giroux",
         pub_year=2011, language="en", pages=499, genre="Business", subgenre="Psychology",
         description="A Nobel laureate explains the two systems that drive human thought — fast, "
                      "intuitive judgment and slow, deliberate reasoning — and where each fails us.",
         subjects=["psychology", "decision-making", "cognitive bias", "economics", "behavior"],
         historical_period="Contemporary", country_setting=None, time_setting="Present Day",
         avg_rating=4.19, rating_count=590000),

    # ---------------- YOUNG ADULT (more) ----------------
    dict(title="Divergent", subtitle=None, authors=["Veronica Roth"],
         isbn13="9780062024039", isbn10=None, publisher="Katherine Tegen Books",
         pub_year=2011, language="en", pages=487, genre="Young Adult", subgenre="Dystopian",
         description="In a future Chicago divided into rigid personality factions, a girl who "
                      "doesn't fit any single category discovers a conspiracy threatening her world.",
         subjects=["dystopia", "identity", "rebellion", "coming-of-age", "factions"],
         historical_period="Future", country_setting="USA", time_setting="Post-Apocalyptic",
         avg_rating=4.19, rating_count=3100000),

    dict(title="Six of Crows", subtitle=None, authors=["Leigh Bardugo"],
         isbn13="9781627792127", isbn10=None, publisher="Henry Holt and Co.",
         pub_year=2015, language="en", pages=465, genre="Young Adult", subgenre="Fantasy",
         description="A crew of six dangerous outcasts is recruited for a seemingly impossible "
                      "heist that could make them rich — or get them all killed.",
         subjects=["heist", "found family", "magic", "crime", "loyalty"],
         historical_period="Fantasy World", country_setting="Fantasy World", time_setting="Fantasy Era",
         avg_rating=4.49, rating_count=750000),

    # ---------------- COOKING / LIFESTYLE ----------------
    dict(title="Salt, Fat, Acid, Heat", subtitle="Mastering the Elements of Good Cooking",
         authors=["Samin Nosrat"],
         isbn13="9781476753836", isbn10=None, publisher="Simon & Schuster",
         pub_year=2017, language="en", pages=480, genre="Cooking", subgenre="Culinary Reference",
         description="A chef breaks cooking down into four foundational elements, teaching intuition "
                      "over recipes so readers can cook confidently from any cuisine.",
         subjects=["cooking", "culinary technique", "flavor", "food science", "recipes"],
         historical_period="Contemporary", country_setting=None, time_setting="Present Day",
         avg_rating=4.55, rating_count=45000),

    # ---------------- TRAVEL / ADVENTURE ----------------
    dict(title="Into the Wild", subtitle=None, authors=["Jon Krakauer"],
         isbn13="9780385486804", isbn10=None, publisher="Villard",
         pub_year=1996, language="en", pages=207, genre="Nonfiction", subgenre="Adventure/True Story",
         description="A journalist reconstructs the final journey of a young man who gave away his "
                      "savings and walked into the Alaskan wilderness, where he starved to death.",
         subjects=["wilderness", "adventure", "idealism", "isolation", "true story"],
         historical_period="Contemporary", country_setting="USA", time_setting="1990s",
         avg_rating=3.98, rating_count=470000),

    # ---------------- GRAPHIC NOVEL ----------------
    dict(title="Maus", subtitle="A Survivor's Tale", authors=["Art Spiegelman"],
         isbn13="9780679406419", isbn10=None, publisher="Pantheon Books",
         pub_year=1980, language="en", pages=296, genre="Graphic Novel", subgenre="Historical",
         description="A graphic memoir depicting the author's father's experience surviving the "
                      "Holocaust, rendered with Jews as mice and Nazis as cats.",
         subjects=["Holocaust", "memoir", "family", "trauma", "World War II"],
         historical_period="World War II", country_setting="Poland/USA", time_setting="1930s-1980s",
         avg_rating=4.34, rating_count=180000),

    dict(title="Watchmen", subtitle=None, authors=["Alan Moore", "Dave Gibbons"],
         isbn13="9781401245252", isbn10=None, publisher="DC Comics",
         pub_year=1987, language="en", pages=416, genre="Graphic Novel", subgenre="Superhero/Deconstruction",
         description="A murder investigation among retired vigilantes unravels a conspiracy that "
                      "deconstructs the superhero genre against the backdrop of nuclear paranoia.",
         subjects=["superheroes", "conspiracy", "morality", "Cold War", "vigilantism"],
         historical_period="Alternate 1980s", country_setting="USA", time_setting="1980s",
         avg_rating=4.32, rating_count=270000),

    # ---------------- CLASSIC WORLD LITERATURE ----------------
    dict(title="Things Fall Apart", subtitle=None, authors=["Chinua Achebe"],
         isbn13="9780385474542", isbn10=None, publisher="Anchor Books",
         pub_year=1958, language="en", pages=209, genre="Classics", subgenre="African Literature",
         description="A respected Igbo leader's world unravels as British colonialism and "
                      "Christian missionaries disrupt the traditions and values of his village.",
         subjects=["colonialism", "tradition", "identity", "masculinity", "Africa"],
         historical_period="Late 19th century", country_setting="Nigeria", time_setting="1890s",
         avg_rating=3.92, rating_count=280000),
]
