plugins {
    id("com.android.application")
}

android {
    namespace = "com.dafeiyu.pet"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.dafeiyu.pet"
        minSdk = 26
        targetSdk = 33
        versionCode = 2
        versionName = "1.1"
    }

    // 先声明签名配置，buildTypes 里才能取到
    signingConfigs {
        create("petDebug") {
            // 调试签名放在工程外层的 android-build 目录，避免写到用户目录被拦
            storeFile = file("../../android-build/debug.keystore")
            storePassword = "android"
            keyAlias = "androiddebugkey"
            keyPassword = "android"
        }
    }

    buildTypes {
        debug {
            signingConfig = signingConfigs.getByName("petDebug")
        }
        release {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
