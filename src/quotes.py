import random

QUOTES = [
    {"text": "Know thyself, for in that knowledge lies the universe.", "author": "G.I. Gurdjieff", "category": "Gurdjieff"},
    {"text": "Be present in the now, the only moment you truly have.", "author": "G.I. Gurdjieff", "category": "Gurdjieff"},
    {"text": "Confront your inner world to understand the outer world.", "author": "G.I. Gurdjieff", "category": "Gurdjieff"},
    {"text": "Seek the truth within, for only then can you see it without.", "author": "G.I. Gurdjieff", "category": "Gurdjieff"},
    {"text": "Awaken to your own sleep, and begin the journey to consciousness.", "author": "G.I. Gurdjieff", "category": "Gurdjieff"},
    {"text": "Every action, every thought, requires your full presence.", "author": "G.I. Gurdjieff", "category": "Gurdjieff"},
    {"text": "Remember your aim, for without it, you are but a leaf in the wind.", "author": "G.I. Gurdjieff", "category": "Gurdjieff"},
    {"text": "Self-observation is the mirror to your soul's awakening.", "author": "G.I. Gurdjieff", "category": "Gurdjieff"},
    {"text": "Let your intentions guide your actions, not your habits.", "author": "G.I. Gurdjieff", "category": "Gurdjieff"},
    {"text": "The struggle within is the path to true freedom.", "author": "G.I. Gurdjieff", "category": "Gurdjieff"},
    {"text": "Do not merely exist; strive to live consciously.", "author": "G.I. Gurdjieff", "category": "Gurdjieff"},
    {"text": "Embrace the unknown, for it is the cradle of growth.", "author": "G.I. Gurdjieff", "category": "Gurdjieff"},
    {"text": "The present moment is the doorway to eternity.", "author": "G.I. Gurdjieff", "category": "Gurdjieff"},
    {"text": "Conscious work is the key to unlock your potential.", "author": "G.I. Gurdjieff", "category": "Gurdjieff"},
    {"text": "Resist the comfort of sleep; embrace the challenge of awakening.", "author": "G.I. Gurdjieff", "category": "Gurdjieff"},
    {"text": "The soul of the true poet is a little unclouded.", "author": "William Blake", "category": "Blake"},
    {"text": "To see a world in a grain of sand, and a heaven in a wild flower.", "author": "William Blake", "category": "Blake"},
    {"text": "What is now proved was once only imagined.", "author": "William Blake", "category": "Blake"},
    {"text": "No bird soars too high if he soars with his own wings.", "author": "William Blake", "category": "Blake"},
    {"text": "A truth that's told with bad intent beats all the lies you can invent.", "author": "William Blake", "category": "Blake"},
    {"text": "Great things are done when men and mountains meet.", "author": "William Blake", "category": "Blake"},
    {"text": "If the doors of perception were cleansed everything would appear to man as it is, infinite.", "author": "William Blake", "category": "Blake"},
    {"text": "The tree which moves some to tears of joy is in the eyes of others only a green thing that stands in the way.", "author": "William Blake", "category": "Blake"},
    {"text": "He who binds to himself a joy does the winged life destroy; but he who kisses the joy as it flies lives in eternity's sunrise.", "author": "William Blake", "category": "Blake"},
    {"text": "The wound is the place where the Light enters you.", "author": "Rumi", "category": "Rumi"},
    {"text": "What you seek is seeking you.", "author": "Rumi", "category": "Rumi"},
    {"text": "Don't be satisfied with stories, how things have gone with others.", "author": "Rumi", "category": "Rumi"},
    {"text": "Let yourself be silently drawn by the strange pull of what you really love.", "author": "Rumi", "category": "Rumi"},
    {"text": "Stop acting so small. You are the universe in ecstatic motion.", "author": "Rumi", "category": "Rumi"},
    {"text": "Yesterday I was clever, so I wanted to change the world. Today I am wise, so I am changing myself.", "author": "Rumi", "category": "Rumi"},
    {"text": "Raise your words, not voice. It is rain that grows flowers, not thunder.", "author": "Rumi", "category": "Rumi"},
    {"text": "The universe is not outside of you. Look inside yourself; everything that you want, you already are.", "author": "Rumi", "category": "Rumi"},
    {"text": "You were born with wings, why prefer to crawl through life?", "author": "Rumi", "category": "Rumi"},
    {"text": "When you do things from your soul, you feel a river moving in you, a joy.", "author": "Rumi", "category": "Rumi"},
    {"text": "The river that flows in you also flows in me.", "author": "Kabir", "category": "Kabir"},
    {"text": "Wherever you are is the entry point.", "author": "Kabir", "category": "Kabir"},
    {"text": "The moon stays bright when it doesn't avoid the night.", "author": "Kabir", "category": "Kabir"},
    {"text": "Your own self-realization is the greatest service you can render the world.", "author": "Kabir", "category": "Kabir"},
    {"text": "Even after all this time, the sun never says to the earth, 'You owe me.'", "author": "Kabir", "category": "Kabir"},
    {"text": "Life is a balance between holding on and letting go.", "author": "Kabir", "category": "Kabir"},
    {"text": "Love is the bridge between you and everything.", "author": "Kabir", "category": "Kabir"},
    {"text": "Where are you? Declare the purpose and set your heart free.", "author": "Kabir", "category": "Kabir"},
    {"text": "In the midst of movement and chaos, keep stillness inside of you.", "author": "Kabir", "category": "Kabir"},
    {"text": "Love is the bond of all life.", "author": "Meher Baba", "category": "Meher Baba"},
    {"text": "Your heart is the door to the soul, but you must turn the key.", "author": "Meher Baba", "category": "Meher Baba"},
    {"text": "In the end, there is no saving anyone but yourself.", "author": "Meher Baba", "category": "Meher Baba"},
    {"text": "Your journey has just begun.", "author": "Meher Baba", "category": "Meher Baba"},
    {"text": "The love you give comes back to you as love you receive.", "author": "Meher Baba", "category": "Meher Baba"},
    {"text": "To realize the truth, you must eliminate all that is not truth.", "author": "Meher Baba", "category": "Meher Baba"},
    {"text": "Happiness is not outside; it is inside.", "author": "Meher Baba", "category": "Meher Baba"},
    {"text": "Be still, for the One is near.", "author": "Meher Baba", "category": "Meher Baba"},
    {"text": "The seeker must become the sought.", "author": "Meher Baba", "category": "Meher Baba"},
    {"text": "Live your life as if you were to die tomorrow.", "author": "Meher Baba", "category": "Meher Baba"},
    {"text": "Man is not a human being having a spiritual experience. He is a spiritual being having a human experience.", "author": "P.D. Ouspensky", "category": "Ouspensky"},
    {"text": "Nothing in this world can be done without pure consciousness.", "author": "P.D. Ouspensky", "category": "Ouspensky"},
    {"text": "The only thing that is real is the present moment.", "author": "P.D. Ouspensky", "category": "Ouspensky"},
    {"text": "Man is the most powerful and the most ignorant of all beings.", "author": "P.D. Ouspensky", "category": "Ouspensky"},
    {"text": "Self-remembering is the core of all progress in life.", "author": "P.D. Ouspensky", "category": "Ouspensky"},
    {"text": "A true focus is in the development of self-awareness.", "author": "P.D. Ouspensky", "category": "Ouspensky"},
    {"text": "The rational mind is a device for seeking truth.", "author": "P.D. Ouspensky", "category": "Ouspensky"},
    {"text": "Understanding arises from deep inquiry.", "author": "P.D. Ouspensky", "category": "Ouspensky"},
    {"text": "Only through direct experience can we truly know.", "author": "P.D. Ouspensky", "category": "Ouspensky"},
    {"text": "To know others is intelligence; to know yourself is true wisdom.", "author": "Lao-Tzu", "category": "Lao-Tzu"},
    {"text": "Meditate on love, compassion, and enlightenment.", "author": "Milarepa", "category": "Others"},
    {"text": "Keep your mind in the depths of hell, and despair not.", "author": "Silouan the Athonite", "category": "Others"},
    {"text": "Find the truth in your heart, and let it light your path.", "author": "Bahauddin Naqshband", "category": "Others"},
    {"text": "Seek wisdom with humility and you will find it in abundance.", "author": "Al Ghazali", "category": "Others"},
    {"text": "Justice, justice shall you pursue.", "author": "Moses", "category": "Others"},
    {"text": "The earth shall give back what it owes to life.", "author": "Yunus Emre", "category": "Others"},
]

def get_categories():
    return sorted(set(q["category"] for q in QUOTES))

class QuoteRotator:
    def __init__(self, categories=None):
        self._last = None
        self._categories = categories

    def set_categories(self, categories):
        self._categories = categories if categories else None

    def _pool(self):
        if not self._categories:
            return QUOTES
        return [q for q in QUOTES if q["category"] in self._categories]

    def next(self):
        pool = self._pool()
        if not pool:
            pool = QUOTES
        for _ in range(50):
            q = random.choice(pool)
            if q != self._last or len(pool) == 1:
                self._last = q
                return q
        self._last = pool[0]
        return pool[0]

    def format(self, q):
        return f"{q['text']} — {q['author']}"
