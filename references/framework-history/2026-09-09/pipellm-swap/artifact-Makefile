SRCS = $(wildcard ./*.cpp)
OBJS = $(patsubst ./%.cpp, ./%.o, $(SRCS))
#-ltcmalloc
%.o: %.cpp pipellm.h
	g++ -c -lpthread -lcuda -lcudart \
	-I/usr/local/cuda/targets/x86_64-linux/include \
	-Wl,--version-script=pipellm.ver \
	-fpic -O2 -g -march=native $< -o $@

all: $(OBJS)
	rm -f ./*.so*
	g++ -shared -o libcrypto.so.3 \
	-Wl,--version-script=pipellm.ver \
	-Wl,--allow-multiple-definition \
	-Wl,--whole-archive $(OBJS) \
	-Wl,--whole-archive ./libcrypto.a -Wl,--no-whole-archive \
	-Wl,-lcuda \
	-Wl,-L/usr/local/cuda/targets/x86_64-linux/lib/ -Wl,-lcudart
