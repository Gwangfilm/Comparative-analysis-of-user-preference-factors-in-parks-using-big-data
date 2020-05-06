# Comparative-analysis-of-user-preference-factors-in-parks-using-big-data
-Using big data from the Google map reviews and LDA2VEC topic modeling method
LDA2VEC-pytorch was written by https://github.com/TropComplique/lda2vec-pytorch


본 프로젝트는 서울시립대학교 조경학과 2020년 졸업작품과정에서 작성된 코드 기록용입니다.
1월부터 Python for everybody(PY4E)를 통해 파이썬을 독학한 뒤 웹 크롤링부터 토픽모델링까지 적절히 소스를 참고해가며 구현하였습니다.
배움이 짧은 만큼 코드에 미흡한 부분도 많은 점 양해 부탁드리며 더 나은 코드작성법을 조언해 주시면 깊게 새겨듣겠습니다.

기존 구글 api로는 리뷰를 5개밖에 얻지 못하여서 셀레니움방식으로도 크롤링을 해보았지만 리뷰가 대략 1500개정도가 누적되면 구글 맵 페이지 자체에서 스택초과 에러가 발생하여서 직접 서버에서 리뷰를 받아오는 url을 활용하였습니다. 

LDA2VEC모델의 경우 버전차이로 인해 제대로 작동이 되지 않아서 아나콘다3의 주피터노트북 파이썬 3.7.6 64bit기준으로 디버깅을 하였고 이외에 변수를 따로 조작하지는 않았습니다. 안에 스크립트가 이것저것 테스트하느라 다소 난잡하게 분포되어 있습니다.
