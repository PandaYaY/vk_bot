1. заходим в папку vk_bot/bot,
  собираем образ: docker build -t bot .
  
2. переходим в папку vk_bot/take_lessons,
  собираем образ: docker build -t lessons .
  
3. возвращаемся в папку vk_bot,
  собираем docker-compose: docker-compose up -d --force-recreate
  
- для просмотра логов использовать: docker-compose logs -f имя_сервиса
  - -f(динамический просмотр) 
  - имя_сервиса: bot или lessons
