# Available Fish Audio Voice Models

Based on your Fish Audio account, here are the available voice models you can use:

## English Voices (Good for News Briefings)

### 1. **Elon Musk (Noise Reduction)**
- **Model ID**: `03397b4c4be74759b72533b663fbd001`
- **Language**: English
- **Description**: Tech-focused, articulate voice with noise reduction
- **Sample**: Talks about signal processing and AI
- **Popularity**: 1366 likes, used 436,676 times

### 2. **SpongeBob SquarePants**
- **Model ID**: `54e3a85ac9594ffa83264b8a494b901b`
- **Language**: English
- **Description**: Energetic, animated voice
- **Sample**: Enthusiastic and cheerful tone
- **Popularity**: 711 likes, used 208,809 times

### 3. **Donald J. Trump (Noise Reduction)**
- **Model ID**: `5196af35f6ff4a0dbf541793fc9f2157`
- **Language**: English
- **Description**: Authoritative, confident delivery
- **Sample**: Business and technology focused
- **Popularity**: 1043 likes, used 196,699 times

### 4. **Energetic Male** ⭐ (Recommended for News)
- **Model ID**: `802e3bc2b27e49c2995d23ef70e6ac89`
- **Language**: English
- **Description**: Professional, energetic male voice
- **Sample**: Professional announcements and sales
- **Popularity**: 780 likes, used 169,042 times

## Chinese Voices

### 5. **丁真 (Ding Zhen)**
- **Model ID**: `54a5170264694bfc8e9ad98df7bd89c3`
- **Language**: Chinese
- **Popularity**: 5085 likes, used 380,594 times

### 6. **AD学姐**
- **Model ID**: `7f92f8afb8ec43bf81429cc1c9199cb1`
- **Language**: Chinese
- **Tags**: 女友感, 御姐, 舒缓 (Girlfriend feel, mature woman, soothing)
- **Popularity**: 3355 likes, used 270,089 times

### 7. **赛马娘**
- **Model ID**: `0eb38bc974e1459facca38b359e13511`
- **Language**: Chinese
- **Description**: 脑残，可爱 (Silly, cute)
- **Popularity**: 2586 likes, used 169,830 times

## Arabic Voices

### 8. **عصام الشوالي (Issam El Shawali)**
- **Model ID**: `5b67899dc9a34685ae09c94c890a606f`
- **Language**: Arabic
- **Description**: Sports commentator style
- **Popularity**: 3149 likes, used 323,024 times

### 9. **حفيظ دراجي (Hafid Derradji)**
- **Model ID**: `d1e9fc34d3704984a9a25c1b3ea4f091`
- **Language**: Arabic
- **Description**: Professional news/sports commentary
- **Popularity**: 1255 likes, used 155,076 times

### 10. **فارس عوض (Faris Awad)**
- **Model ID**: `79b0fd32e00645e2827b841629034be5`
- **Language**: Arabic
- **Description**: Motivational, philosophical tone
- **Popularity**: 1069 likes, used 150,158 times

## Recommended for Market Briefings

For your market briefings, I recommend trying these voices:

1. **Energetic Male** (`802e3bc2b27e49c2995d23ef70e6ac89`) - Professional and clear
2. **Elon Musk** (`03397b4c4be74759b72533b663fbd001`) - Tech-savvy and articulate
3. **Donald Trump** (`5196af35f6ff4a0dbf541793fc9f2157`) - Authoritative business tone

## How to Use

Add one of these model IDs to your `.env` file:

```bash
FISH_API_KEY=your_api_key
FISH_MODEL_ID=802e3bc2b27e49c2995d23ef70e6ac89  # Energetic Male voice
```

Then all your audio generations will use that consistent voice!

## Testing Different Voices

Run the test script to hear samples:
```bash
./test_fish_voices.py
```

This will generate sample audio files for each voice so you can compare them.