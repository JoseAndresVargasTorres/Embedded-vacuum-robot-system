cmake_minimum_required(VERSION 3.10)
project(libcontrol)

# Crear biblioteca compartida
add_library(control SHARED libcontrol.c)

# Incluir headers
target_include_directories(control PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

# Instalar biblioteca y header
install(TARGETS control DESTINATION ${CMAKE_INSTALL_LIBDIR})
install(FILES libcontrol.h DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})
