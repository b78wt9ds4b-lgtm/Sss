/*
 * DART — migliorie per il sito WordPress darthome.it
 *
 * Dove incollarlo: plugin WPCode → Code Snippets → + Add Snippet → «Add Your Custom Code»,
 * tipo «PHP Snippet», inserimento «Auto Insert», posizione «Run Everywhere». Poi attivalo.
 * Per i ragazzi: va bene anche in fondo al functions.php del tema dart-child.
 *
 * Ogni parte si accende e si spegne qui sotto (true = accesa, false = spenta).
 * Non tocca prodotti, prezzi, ordini o pagamenti: cambia solo quello che si vede nelle pagine.
 */

if ( ! defined( 'DART_MIGLIORIE' ) ) :
	define( 'DART_MIGLIORIE', '1.0' );

	define( 'DART_WHATSAPP', '393662936810' );  // numero WhatsApp con il prefisso 39, senza spazi né +
	define( 'DART_SEO', true );                  // descrizione per Google, anteprime per WhatsApp e social, dati strutturati
	define( 'DART_SCHEDA', true );               // sotto «Acquista»: WhatsApp, garanzie, misure in scala, condivisione
	define( 'DART_ACQUISTA_ORA', true );         // il pulsante diventa «Acquista ora» e porta subito al pagamento
	define( 'DART_WHATSAPP_FLOTTANTE', true );   // pulsante WhatsApp tondo in basso a destra
	define( 'DART_TESTI_SPEDIZIONE', true );     // testi aggiornati: BRT o Poste Italiane, consegna al piano strada
	define( 'DART_NOTE_ORDINE', true );          // suggerimento nel campo «Note sull'ordine» del pagamento
	define( 'DART_CORRELATI_DISPONIBILI', true ); // tra i «Prodotti correlati» solo pezzi ancora in vendita
	define( 'DART_GALLERIA_TASTIERA', true );    // la galleria della scheda si scorre anche con la tastiera

	/* ------------------------------------------------------------ utilità */

	function dart_wa( $testo, $numero = DART_WHATSAPP ) {
		return 'https://wa.me/' . $numero . '?text=' . rawurlencode( $testo );
	}

	function dart_testo_semplice( $html ) {
		return trim( preg_replace( '/\s+/u', ' ', html_entity_decode( wp_strip_all_tags( (string) $html ), ENT_QUOTES, 'UTF-8' ) ) );
	}

	function dart_riassunto( $html, $max = 155 ) {
		$testo = dart_testo_semplice( $html );
		if ( mb_strlen( $testo ) <= $max ) {
			return $testo;
		}
		$taglio = preg_replace( '/\s+\S*$/u', '', mb_substr( $testo, 0, $max ) ); // taglia all'ultima parola intera
		return rtrim( $taglio, ',.;:— ' ) . '…';
	}

	/** «mobili», «quadri», «sculture» o '' secondo la categoria del pezzo. */
	function dart_categoria( $id ) {
		$mappa = array( 'mobili' => 'mobili', 'quadri-e-ritratti' => 'quadri', 'altro-arredamento' => 'sculture' );
		$termini = get_the_terms( $id, 'product_cat' );
		if ( is_array( $termini ) ) {
			foreach ( $termini as $t ) {
				if ( isset( $mappa[ $t->slug ] ) ) {
					return $mappa[ $t->slug ];
				}
			}
		}
		return '';
	}

	function dart_euro( $valore ) {
		$valore = (float) $valore;
		$decimali = ( floor( $valore ) == $valore ) ? 0 : 2;
		return number_format( $valore, $decimali, ',', '.' ) . ' €';
	}

	/** «H 199 · L 110 · P 50 cm» dalle dimensioni WooCommerce (altezza, larghezza, profondità). */
	function dart_misure( $prodotto ) {
		$parti = array();
		foreach ( array( 'H' => $prodotto->get_height(), 'L' => $prodotto->get_width(), 'P' => $prodotto->get_length() ) as $lettera => $valore ) {
			if ( '' !== (string) $valore && (float) $valore > 0 ) {
				$parti[] = $lettera . ' ' . str_replace( '.', ',', (string) (float) $valore );
			}
		}
		return $parti ? implode( ' · ', $parti ) . ' cm' : '';
	}

	function dart_icona_whatsapp() {
		return '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2Zm0 18.2a8.2 8.2 0 0 1-4.2-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2Zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8-.2-.1-.4-.1-.6.1l-.8 1c-.1.2-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.2-.4.3-.4.8-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.2 5.2 5.2 0 0 0 1.1 2.8 11.9 11.9 0 0 0 4.6 4c1.7.7 2.3.8 3.2.6.5-.1 1.5-.6 1.8-1.2.2-.6.2-1.1.1-1.2l-.4-.2Z"/></svg>';
	}

	/* ------------------------------------------------------------ Google e anteprime social */

	if ( DART_SEO ) {
		add_action( 'wp_head', 'dart_seo', 2 );
		// I dati del prodotto per Google li scrive dart_seo: WooCommerce non deve aggiungerne un secondo blocco.
		add_filter( 'woocommerce_structured_data_product', '__return_empty_array' );
	}

	function dart_seo() {
		// Se c'è già un plugin SEO, decide lui.
		if ( defined( 'WPSEO_VERSION' ) || class_exists( 'RankMath' ) || defined( 'AIOSEO_VERSION' ) || defined( 'SEOPRESS_VERSION' ) ) {
			return;
		}
		$sito        = 'DART';
		$titolo      = wp_get_document_title();
		$descrizione = 'Mobili d’epoca restaurati e dipinti a mano, quadri originali e piccole sculture in legno. Pezzi unici dal laboratorio di Trieste, spedizione in tutta Italia.';
		$url         = ''; // l'indirizzo della pagina, se è una di quelle che conosciamo
		$immagine    = get_stylesheet_directory_uri() . '/assets/img/hero.jpg';
		$tipo        = 'website';
		$extra       = '';
		$schema      = array();

		if ( function_exists( 'is_product' ) && is_product() ) {
			$prodotto = wc_get_product( get_queried_object_id() );
			if ( $prodotto ) {
				$url    = get_permalink( $prodotto->get_id() );
				$misure = dart_misure( $prodotto );
				$testo  = dart_testo_semplice( $prodotto->get_description() ? $prodotto->get_description() : $prodotto->get_short_description() );
				$frasi  = preg_split( '/(?<=[.!?])\s/u', $testo );
				$parti  = array_filter( array( '' !== $testo ? dart_riassunto( $frasi[0], 100 ) : $prodotto->get_name(), $misure ) );
				if ( $prodotto->get_price() !== '' ) {
					$parti[] = dart_euro( $prodotto->get_price() );
				}
				$parti[]     = $prodotto->is_in_stock() ? 'Pezzo unico, spedizione in tutta Italia' : 'Venduto';
				$descrizione = dart_riassunto( implode( ' · ', $parti ), 160 );
				$tipo        = 'product';
				$immagini    = array();
				foreach ( array_merge( array( $prodotto->get_image_id() ), $prodotto->get_gallery_image_ids() ) as $id_img ) {
					$src = $id_img ? wp_get_attachment_image_url( $id_img, 'large' ) : '';
					if ( $src ) {
						$immagini[] = $src;
					}
				}
				if ( $immagini ) {
					$immagine = $immagini[0];
				}
				if ( $prodotto->get_price() !== '' ) {
					$extra .= '<meta property="product:price:amount" content="' . esc_attr( wc_format_decimal( $prodotto->get_price(), 2 ) ) . '">' . "\n";
					$extra .= '<meta property="product:price:currency" content="EUR">' . "\n";
				}
				$categoria = dart_categoria( $prodotto->get_id() );
				$offerta   = array(
					'@type'                   => 'Offer',
					'url'                     => $url,
					'price'                   => wc_format_decimal( $prodotto->get_price(), 2 ),
					'priceCurrency'           => 'EUR',
					'availability'            => $prodotto->is_in_stock() ? 'https://schema.org/InStock' : 'https://schema.org/SoldOut',
					'itemCondition'           => 'mobili' === $categoria ? 'https://schema.org/RefurbishedCondition' : 'https://schema.org/NewCondition',
					'seller'                  => array( '@type' => 'Organization', 'name' => $sito ),
					'hasMerchantReturnPolicy' => array(
						'@type'                => 'MerchantReturnPolicy',
						'applicableCountry'    => 'IT',
						'returnPolicyCategory' => 'https://schema.org/MerchantReturnFiniteReturnWindow',
						'merchantReturnDays'   => 14,
						'returnMethod'         => 'https://schema.org/ReturnByMail',
						'returnFees'           => 'https://schema.org/ReturnShippingFees',
					),
				);
				$voce = array(
					'@context'    => 'https://schema.org',
					'@type'       => 'Product',
					'name'        => $prodotto->get_name(),
					'description' => '' !== $testo ? dart_riassunto( $testo, 500 ) : $prodotto->get_name(),
					'sku'         => $prodotto->get_sku() ? $prodotto->get_sku() : $prodotto->get_slug(),
					'url'         => $url,
					'brand'       => array( '@type' => 'Brand', 'name' => $sito ),
				);
				if ( $immagini ) {
					$voce['image'] = $immagini;
				}
				// Senza prezzo (vecchi pezzi in archivio) Google considererebbe la scheda incompleta: meglio niente.
				if ( $prodotto->get_price() !== '' ) {
					$voce['offers'] = $offerta;
					$schema[]       = $voce;
				}
			}
		} elseif ( function_exists( 'is_product_category' ) && is_product_category() ) {
			$termine = get_queried_object();
			$link    = get_term_link( $termine );
			if ( ! is_wp_error( $link ) ) {
				$url = $link;
			}
			$testi = array(
				'mobili'            => 'Credenze, cassettiere, armadi, tavoli e sedute d’epoca: restaurati e dipinti a mano, uno alla volta.',
				'quadri-e-ritratti' => 'Dipinti originali ad acrilico su tela e su legno, firmati. Composizioni floreali e ritratti.',
				'altro-arredamento' => 'Piccole sculture in legno dipinto, nate anche dai frammenti dei mobili restaurati.',
			);
			if ( ! empty( $termine->description ) ) {
				$descrizione = dart_riassunto( $termine->description );
			} elseif ( isset( $testi[ $termine->slug ] ) ) {
				$descrizione = $testi[ $termine->slug ] . ' Spedizione in tutta Italia con BRT o Poste Italiane.';
			} else {
				$descrizione = $termine->name . ': pezzi unici dal laboratorio DART di Trieste. Spedizione in tutta Italia con BRT o Poste Italiane.';
			}
		} elseif ( is_front_page() ) {
			$url      = home_url( '/' );
			$schema[] = array(
				'@context'                  => 'https://schema.org',
				'@type'                     => 'FurnitureStore',
				'name'                      => $sito,
				'url'                       => home_url( '/' ),
				'image'                     => $immagine,
				'telephone'                 => '+39 366 293 6810',
				'email'                     => 'assistenza@darthome.it',
				'address'                   => array(
					'@type'           => 'PostalAddress',
					'streetAddress'   => 'Via Luigi Cadorna 13',
					'postalCode'      => '34123',
					'addressLocality' => 'Trieste',
					'addressRegion'   => 'TS',
					'addressCountry'  => 'IT',
				),
				'openingHoursSpecification' => array(
					array( '@type' => 'OpeningHoursSpecification', 'dayOfWeek' => array( 'Tuesday', 'Wednesday', 'Thursday', 'Friday' ), 'opens' => '10:00', 'closes' => '13:00' ),
					array( '@type' => 'OpeningHoursSpecification', 'dayOfWeek' => array( 'Tuesday', 'Wednesday', 'Thursday', 'Friday' ), 'opens' => '16:00', 'closes' => '19:00' ),
					array( '@type' => 'OpeningHoursSpecification', 'dayOfWeek' => array( 'Saturday' ), 'opens' => '10:00', 'closes' => '13:00' ),
				),
				'sameAs'                    => array( 'https://www.instagram.com/dart_trieste_/', 'https://www.facebook.com/shabbychicantiquetochic/' ),
				'vatID'                     => 'IT01429660325',
			);
		} elseif ( function_exists( 'is_shop' ) && is_shop() ) {
			$url         = wc_get_page_permalink( 'shop' );
			$descrizione = 'Tutti i pezzi disponibili: mobili d’epoca restaurati e dipinti a mano, quadri originali e sculture in legno. Spedizione in tutta Italia.';
		} elseif ( is_singular() ) {
			$url   = get_permalink();
			$testo = has_excerpt() ? get_the_excerpt() : get_post_field( 'post_content', get_queried_object_id() );
			if ( dart_testo_semplice( $testo ) ) {
				$descrizione = dart_riassunto( $testo );
			}
		}

		echo "\n<!-- DART: descrizione, anteprime social e dati per Google -->\n";
		echo '<meta name="description" content="' . esc_attr( $descrizione ) . '">' . "\n";
		echo '<meta property="og:type" content="' . esc_attr( $tipo ) . '">' . "\n";
		echo '<meta property="og:site_name" content="' . esc_attr( $sito ) . '">' . "\n";
		echo '<meta property="og:locale" content="it_IT">' . "\n";
		echo '<meta property="og:title" content="' . esc_attr( $titolo ) . '">' . "\n";
		echo '<meta property="og:description" content="' . esc_attr( $descrizione ) . '">' . "\n";
		if ( $url ) {
			echo '<meta property="og:url" content="' . esc_url( $url ) . '">' . "\n";
		}
		echo '<meta property="og:image" content="' . esc_url( $immagine ) . '">' . "\n";
		echo $extra; // già sanificato sopra
		echo '<meta name="twitter:card" content="summary_large_image">' . "\n";
		foreach ( $schema as $voce ) {
			echo '<script type="application/ld+json">' . wp_json_encode( $voce, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES ) . '</script>' . "\n";
		}
	}

	/* ------------------------------------------------------------ scheda pezzo */

	if ( DART_SCHEDA ) {
		add_action( 'woocommerce_after_add_to_cart_form', 'dart_scheda', 20 );
	}

	function dart_scheda() {
		global $product;
		if ( ! $product instanceof WC_Product ) {
			return;
		}
		$nome      = $product->get_name();
		$url       = get_permalink( $product->get_id() );
		$garanzia  = 'quadri' === dart_categoria( $product->get_id() ) ? '24 mesi' : '12 mesi';
		$domanda   = 'Ciao DART, mi interessa «' . $nome . '» (' . $url . '). Potreste mandarmi altre foto o un video?';
		$condividi = 'https://wa.me/?text=' . rawurlencode( $nome . ' — ' . $url );
		echo '<div class="dart-scheda">'
			. '<a class="dart-whatsapp" href="' . esc_url( dart_wa( $domanda ) ) . '" target="_blank" rel="noopener">' . dart_icona_whatsapp() . 'Chiedi altre foto o un video</a>'
			. '<p class="dart-unico">Ne esiste uno solo: quando è venduto, non torna.</p>'
			. '<ul class="dart-garanzie">'
			. '<li><strong>Pagamento sicuro</strong> con carta, Apple Pay, Google Pay o bonifico</li>'
			. '<li><strong>Reso entro 14 giorni</strong>, senza dover spiegare il motivo</li>'
			. '<li><strong>Garanzia di ' . esc_html( $garanzia ) . '</strong> sul pezzo</li>'
			. '<li><strong>Imballato a mano</strong> e spedito con BRT o Poste Italiane, al piano strada</li>'
			. '</ul>'
			. dart_disegno_misure( $product ) // SVG costruito con soli numeri
			. '<p class="dart-condividi"><a href="' . esc_url( $condividi ) . '" target="_blank" rel="noopener">Condividilo con chi deve decidere con te</a></p>'
			. '</div>';
	}

	/** Il pezzo in scala accanto a una persona alta 170 cm (solo mobili e quadri con altezza e larghezza). */
	function dart_disegno_misure( $prodotto ) {
		$categoria = dart_categoria( $prodotto->get_id() );
		$alt       = (float) $prodotto->get_height();
		$larg      = (float) $prodotto->get_width();
		if ( ! in_array( $categoria, array( 'mobili', 'quadri' ), true ) || $alt <= 0 || $larg <= 0 ) {
			return '';
		}
		$quadro    = 'quadri' === $categoria;
		$persona   = 170;
		$da_terra  = $quadro ? 150 - $alt / 2 : 0;
		$w         = 340;
		$h         = 230;
		$terra     = 200;
		$x_persona = 30;
		$scala     = min( 170 / max( $persona, $da_terra + $alt ), ( $w - $x_persona - 46 - 56 ) / ( $larg + 58 ) );
		$s         = function ( $cm ) use ( $scala ) {
			return round( $cm * $scala, 1 );
		};
		$u   = $s( $persona );
		$px  = $x_persona + $s( 29 );
		$top = $terra - $u;
		$r   = function ( $x, $y, $larghezza, $altezza, $raggio ) {
			return sprintf( '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%.1f"/>', $x, $y, $larghezza, $altezza, $raggio );
		};
		$sagoma = sprintf( '<circle cx="%.1f" cy="%.1f" r="%.1f"/>', $px, $top + 0.075 * $u, 0.07 * $u )
			. $r( $px - 0.12 * $u, $top + 0.16 * $u, 0.24 * $u, 0.39 * $u, 0.05 * $u )
			. $r( $px - 0.17 * $u, $top + 0.17 * $u, 0.04 * $u, 0.35 * $u, 0.02 * $u )
			. $r( $px + 0.13 * $u, $top + 0.17 * $u, 0.04 * $u, 0.35 * $u, 0.02 * $u )
			. $r( $px - 0.105 * $u, $top + 0.53 * $u, 0.095 * $u, 0.47 * $u, 0.03 * $u )
			. $r( $px + 0.01 * $u, $top + 0.53 * $u, 0.095 * $u, 0.47 * $u, 0.03 * $u );
		$x0  = $px + $s( 29 ) + 46;
		$y0  = $terra - $s( $da_terra ) - $s( $alt );
		$fmt = function ( $cm ) {
			return str_replace( '.', ',', (string) (float) $cm );
		};
		$svg = sprintf( '<svg viewBox="0 0 %d %d" role="img" aria-label="%s">', $w, $h, esc_attr( $prodotto->get_name() . ': alto ' . $fmt( $alt ) . ' cm e largo ' . $fmt( $larg ) . ' cm, accanto a una persona alta 170 cm' ) )
			. sprintf( '<line class="dart-terra" x1="10" y1="%d" x2="%d" y2="%d"/>', $terra, $w - 10, $terra )
			. '<g class="dart-persona">' . $sagoma . '</g>'
			. sprintf( '<text x="%.1f" y="%d" text-anchor="middle">1,70 m</text>', $px, $terra + 18 )
			. sprintf( '<rect class="dart-pezzo" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="2"/>', $x0, $y0, $s( $larg ), $s( $alt ) )
			. sprintf( '<line class="dart-quota" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>', $x0, $y0 + $s( $alt ) + 10, $x0 + $s( $larg ), $y0 + $s( $alt ) + 10 )
			. sprintf( '<text x="%.1f" y="%.1f" text-anchor="middle">%s cm</text>', $x0 + $s( $larg ) / 2, $y0 + $s( $alt ) + 24, $fmt( $larg ) )
			. sprintf( '<line class="dart-quota" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>', $x0 + $s( $larg ) + 10, $y0, $x0 + $s( $larg ) + 10, $y0 + $s( $alt ) )
			. sprintf( '<text x="%.1f" y="%.1f">%s cm</text>', $x0 + $s( $larg ) + 16, $y0 + $s( $alt ) / 2 + 4, $fmt( $alt ) )
			. '</svg>';
		$nota = $quadro ? 'appeso con il centro a 1,50 m da terra' : 'appoggiato a terra';
		return '<figure class="dart-misure"><figcaption>Quanto è grande: in scala accanto a una persona alta 1,70 m, ' . $nota . '.</figcaption>' . $svg . '</figure>';
	}

	/* ------------------------------------------------------------ «Acquista ora» */

	if ( DART_ACQUISTA_ORA ) {
		add_filter( 'woocommerce_product_single_add_to_cart_text', 'dart_testo_acquista' );
		add_filter( 'woocommerce_add_to_cart_redirect', 'dart_vai_al_pagamento', 20 );
	}

	function dart_testo_acquista() {
		return 'Acquista ora';
	}

	/** Dalla scheda di un pezzo si va dritti al pagamento: è unico, il carrello sarebbe un passaggio in più. */
	function dart_vai_al_pagamento( $url ) {
		if ( function_exists( 'wc_get_checkout_url' ) && isset( $_REQUEST['add-to-cart'] ) && ! wp_doing_ajax() ) { // phpcs:ignore WordPress.Security.NonceVerification
			return wc_get_checkout_url();
		}
		return $url;
	}

	/* ------------------------------------------------------------ WhatsApp in ogni pagina */

	if ( DART_WHATSAPP_FLOTTANTE ) {
		add_action( 'wp_footer', 'dart_whatsapp_flottante' );
	}

	function dart_whatsapp_flottante() {
		if ( ( function_exists( 'is_cart' ) && is_cart() ) || ( function_exists( 'is_checkout' ) && is_checkout() ) ) {
			return;
		}
		$messaggio = 'Ciao DART, vorrei qualche informazione.';
		if ( function_exists( 'is_product' ) && is_product() ) {
			$id        = get_queried_object_id();
			$messaggio = 'Ciao DART, ho una domanda su «' . get_post_field( 'post_title', $id ) . '» (' . get_permalink( $id ) . ').';
		}
		echo '<a class="dart-whatsapp-flottante" href="' . esc_url( dart_wa( $messaggio ) ) . '" target="_blank" rel="noopener" aria-label="Scrivici su WhatsApp">' . dart_icona_whatsapp() . '</a>';
	}

	/* ------------------------------------------------------------ testi della spedizione */

	// Le frasi scritte nel tema (home e schede) che parlano ancora di consegna al piano e di
	// telefonata dopo l'ordine. Si sostituiscono solo se le trova uguali, parola per parola:
	// quando i ragazzi avranno cambiato i testi nel tema, non serve più e si può spegnere.
	// (La garanzia di 24 mesi su tutto l'hanno già corretta loro: ogni scheda dice la sua.)
	if ( DART_TESTI_SPEDIZIONE ) {
		add_action( 'template_redirect', 'dart_inizia_sostituzioni' );
	}

	function dart_inizia_sostituzioni() {
		if ( is_admin() || is_feed() || wp_doing_ajax() || ( defined( 'REST_REQUEST' ) && REST_REQUEST ) ) {
			return;
		}
		ob_start( 'dart_sostituisci' );
	}

	function dart_sostituisci( $html ) {
		$frasi = array(
			'Spedizione in tutta Italia con corriere. La tariffa è fissa in base al pezzo; per le isole c’è un supplemento.'
				=> 'Spedizione in tutta Italia con BRT o Poste Italiane. La tariffa è fissa in base al pezzo; per Sicilia e Sardegna c’è un supplemento.',
			'Dopo l’ordine ti contattiamo per concordare il giorno di consegna. Nelle note dell’ordine puoi segnalare piano, ascensore o ZTL.'
				=> 'La consegna è al piano strada: il corriere lascia il pezzo all’ingresso dell’edificio. Quando il pezzo parte ti mandiamo il codice per seguire la spedizione.',
			'Ti contattiamo dopo l’ordine per concordare il giorno: di solito i mobili arrivano entro due settimane, quadri e tavolini entro dieci giorni lavorativi. Puoi segnalare piano, ascensore e ZTL nelle note.'
				=> 'Spediamo con BRT o Poste Italiane, con consegna al piano strada: di solito i mobili arrivano entro due settimane, quadri e tavolini entro dieci giorni lavorativi. Quando il pezzo parte ti mandiamo il codice per seguirlo.',
			'Assistenza per la consegna al piano'
				=> 'Consegna al piano strada, con codice di tracciamento',
			'Imballaggio curato, consegna seguita da noi.'
				=> 'Imballaggio curato, spedizione con BRT o Poste Italiane.',
			'La categoria è già pronta: basta caricare i pezzi dal pannello.'
				=> 'Presto in arrivo.',
			'In negozio a Trieste trovi tutti i pezzi dal vivo — e dal vivo, spesso, sono ancora più belli.'
				=> 'Se vuoi vedere meglio un pezzo prima di comprarlo, scrivici su WhatsApp: ti mandiamo altre foto o un video. Poi lo imballiamo a mano e lo spediamo in tutta Italia.',
		);
		return strtr( $html, $frasi );
	}

	/* ------------------------------------------------------------ note dell'ordine */

	if ( DART_NOTE_ORDINE ) {
		add_filter( 'woocommerce_checkout_fields', 'dart_note_ordine' );
	}

	function dart_note_ordine( $campi ) {
		if ( isset( $campi['order']['order_comments'] ) ) {
			$campi['order']['order_comments']['placeholder'] = 'Un numero di telefono a cui rispondi e il nome sul citofono: servono al corriere.';
		}
		return $campi;
	}

	/* ------------------------------------------------------------ prodotti correlati */

	// Nelle schede, «Prodotti correlati» proponeva anche pezzi venduti: a fine pagina, al posto di
	// un pezzo acquistabile, c'era un vicolo cieco. WooCommerce ne cerca più del necessario e poi ne
	// tiene 4, quindi togliere i venduti qui non svuota la sezione.
	if ( DART_CORRELATI_DISPONIBILI ) {
		add_filter( 'woocommerce_related_products', 'dart_correlati_disponibili' );
	}

	function dart_correlati_disponibili( $ids ) {
		return array_values(
			array_filter(
				(array) $ids,
				function ( $id ) {
					$pezzo = wc_get_product( $id );
					return $pezzo && $pezzo->is_in_stock() && $pezzo->is_purchasable();
				}
			)
		);
	}

	/* ------------------------------------------------------------ galleria e tastiera */

	// La galleria delle schede (#galleria) scorre di lato ma non si raggiungeva con il tasto Tab
	// (segnalazione «scrollable-region-focusable» del controllo axe): la rendiamo raggiungibile.
	if ( DART_GALLERIA_TASTIERA ) {
		add_action( 'wp_footer', 'dart_galleria_tastiera', 30 );
	}

	function dart_galleria_tastiera() {
		if ( ! function_exists( 'is_product' ) || ! is_product() ) {
			return;
		}
		echo "<script>(function(){var g=document.getElementById('galleria');if(g&&!g.hasAttribute('tabindex')){g.tabIndex=0;g.setAttribute('role','region');g.setAttribute('aria-label','Foto del pezzo: scorri con le frecce');}})();</script>\n";
	}

	/* ------------------------------------------------------------ domande frequenti */

	// Scrivi [dart_domande] in una pagina (blocco «Shortcode») per mostrare le domande frequenti.
	add_shortcode( 'dart_domande', 'dart_domande' );

	function dart_domande() {
		$domande = array(
			'Quanto costa la spedizione?' => 'Dipende dal pezzo ed è scritta in ogni scheda, prima di pagare: da 15 € per un oggetto piccolo a 150 € per credenze e armadi. Per Sicilia e Sardegna c’è un supplemento di 50 €. Se ti interessano più pezzi, scrivici prima di ordinare: vediamo se si può fare un’unica spedizione.',
			'Il corriere mi porta il mobile in casa?' => 'No: spediamo con BRT o Poste Italiane e la consegna è al piano strada, cioè all’ingresso dell’edificio. Per i mobili più grandi, organizzati con qualcuno che ti aiuti a portarli in casa.',
			'Quanto ci mette ad arrivare?' => 'Di solito i mobili arrivano entro due settimane dall’ordine; quadri, tavolini e oggetti entro dieci giorni lavorativi. Quando il pezzo parte ti mandiamo il codice per seguire la spedizione.',
			'Come posso pagare?' => 'Con carta di credito o debito, Apple Pay e Google Pay, tramite Stripe: i dati della carta non passano da noi. Oppure con bonifico: in quel caso il pezzo resta riservato per te 7 giorni.',
			'Posso restituirlo se cambio idea?' => 'Sì. Hai 14 giorni dalla consegna per recedere, senza dover spiegare il motivo. La spedizione di ritorno è a carico tuo; noi ti rimborsiamo il prezzo e anche le spese di consegna che avevi pagato, sullo stesso metodo di pagamento.',
			'E se arriva danneggiato?' => 'Controlla l’imballo davanti al corriere: se è rovinato, firma la consegna «con riserva» e mandaci subito una foto. Vale comunque la garanzia legale (12 mesi sui mobili restaurati, 24 sui quadri): troviamo insieme la soluzione, senza costi per te.',
			'I colori dal vivo sono come in foto?' => 'Ogni schermo mostra i colori in modo un po’ diverso. Se hai un dubbio, chiedici altre foto o un video su WhatsApp prima di comprare.',
			'I mobili sono nuovi?' => 'No: sono mobili d’epoca, che restauriamo e dipingiamo a mano. Qualche segno del tempo nel legno e piccole irregolarità nella pittura fanno parte del loro carattere.',
		);
		$html   = '<div class="dart-domande">';
		$schema = array( '@context' => 'https://schema.org', '@type' => 'FAQPage', 'mainEntity' => array() );
		foreach ( $domande as $domanda => $risposta ) {
			$html .= '<details><summary>' . esc_html( $domanda ) . '</summary><p>' . esc_html( $risposta ) . '</p></details>';
			$schema['mainEntity'][] = array(
				'@type'          => 'Question',
				'name'           => $domanda,
				'acceptedAnswer' => array( '@type' => 'Answer', 'text' => $risposta ),
			);
		}
		return $html . '</div><script type="application/ld+json">' . wp_json_encode( $schema, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES ) . '</script>';
	}

endif;
